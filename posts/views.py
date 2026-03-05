from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.shortcuts import get_object_or_404

from posts.models import Post, PostMedia, PostLike, Comment
from posts.serializers import PostSerializer, CommentSerializer
from friends.models import Friendship


# Create your views here.

class CreatePostView(APIView):
    # POST -> Create a new post
    # Supports: Text (optional), Multiple images/videos and Visibility selection

    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Extract text and visibility
        content = request.data.get('content')
        visibility = request.data.get('visibility', 'FRIENDS')

        # Get uploaded files (can be multiple)
        files = request.FILES.getlist('media')

        # Validate: must have text or media
        if not content and not files:
            return Response(
                {"error": "Post must contain text or at least one media file."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create Post instance
        post = Post.objects.create(
            author=request.user,
            content=content,
            visibility=visibility
        )

        # Create media objects if provided
        for file in files:
            # Determine media type automatically
            if file.content_type.startswith('image'):
                media_type = 'IMAGE'
            elif file.content_type.startswith('video'):
                media_type = 'VIDEO'
            else:
                post.delete()  # rollback if invalid file
                return Response(
                    {"error": "Only image and video files are allowed."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            PostMedia.objects.create(
                post=post,
                media_type=media_type,
                file=file
            )

        # Serialize and return created post
        serializer = PostSerializer(post, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class FeedView(APIView):
    # Returns: Logged-in user's posts, Friends' posts, Ordered by newest first

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # 1- Get accepted friendships
        friendships = Friendship.objects.filter(
            Q(user1=user) | Q(user2=user)
        )

        # 2- Extract friend IDs
        friend_ids = []

        for friendship in friendships:
            if friendship.user1 == user:
                friend_ids.append(friendship.user2.id)
            else:
                friend_ids.append(friendship.user1.id)

        # 3- Fetch posts (own + friends)
        posts = Post.objects.filter(
            Q(author=user) | Q(author__in=friend_ids)
        ).select_related('author').prefetch_related('media').order_by('-created_at')

        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


def can_interact(user, post):
    # Who can interact with the post e.g. see, like and comment on post

    if post.author == user:
        return True

    if post.visibility == "PUBLIC":
        return True

    if post.visibility == "FRIENDS":
        return Friendship.objects.filter(
            Q(user1=user, user2=post.author) |
            Q(user1=post.author, user2=user)
        ).exists()

    return False


class PostLikeView(APIView):
    # Handles like / dislike (toggle) on a post explicitly via request body

    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        user = request.user
        post = get_object_or_404(Post, id=post_id)

        like_status = request.data.get("like_status")

        # Validate input
        if like_status not in ["like", "dislike"]:
            return Response(
                {"error": "like_status must be 'like' or 'dislike'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        #  Visibility Check (CRITICAL)

        # If post is not authored by current user
        if post.author != user:

            # If visibility is FRIENDS → must be friend
            if post.visibility == "FRIENDS":

                is_friend = Friendship.objects.filter(
                    Q(user1=user, user2=post.author) |
                    Q(user1=post.author, user2=user)
                ).exists()

                if not is_friend:
                    return Response(
                        {"error": "You cannot interact with this post."},
                        status=status.HTTP_403_FORBIDDEN
                    )

        # Like / Unlike Logic
        existing_like = PostLike.objects.filter(
            post=post,
            user=user
        ).first()

        # LIKE
        if like_status == "like":

            if existing_like:
                return Response(
                    {"message": "Post already liked."},
                    status=status.HTTP_200_OK
                )

            PostLike.objects.create(post=post, user=user)

            return Response(
                {"message": "Post liked successfully."},
                status=status.HTTP_201_CREATED
            )

        # DISLIKE (Undo)
        if like_status == "dislike":

            if not existing_like:
                return Response(
                    {"message": "Post is not liked yet."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            existing_like.delete()

            return Response(
                {"message": "Post unliked successfully."},
                status=status.HTTP_200_OK
            )


class CreateCommentView(APIView):
    # Create a comment on a post. Allows multiple comments by same user.

    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        user = request.user
        post = get_object_or_404(Post, id=post_id)

        # Visibility enforcement
        if not can_interact(user, post):
            return Response(
                {"error": "You cannot comment on this post."},
                status=status.HTTP_403_FORBIDDEN
            )

        content = request.data.get("content")

        if not content:
            return Response(
                {"error": "Content is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        comment = Comment.objects.create(
            post=post,
            author=user,
            content=content
        )

        serializer = CommentSerializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CommentModifyView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, custom_id):

        try:
            post_id, comment_number = custom_id.split('-')
        except ValueError:
            return None

        return Comment.objects.filter(
            post_id=post_id,
            comment_number=comment_number
        ).first()

    def put(self, request, custom_id):
        return self.update_comment(request, custom_id)

    def patch(self, request, custom_id):
        return self.update_comment(request, custom_id)

    def update_comment(self, request, custom_id):

        comment = self.get_object(custom_id)

        if not comment:
            return Response(
                {"error": "Invalid comment ID."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Author check
        if comment.author != request.user:
            return Response(
                {"error": "You can only edit your own comment."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = CommentSerializer(
            comment,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, custom_id):

        comment = self.get_object(custom_id)

        if not comment:
            return Response(
                {"error": "Invalid comment ID."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Author check
        if comment.author != request.user:
            return Response(
                {"error": "You can only delete your own comment."},
                status=status.HTTP_403_FORBIDDEN
            )

        comment.delete()

        return Response(
            {"message": "Comment deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )


class DeleteAllPostCommentsView(APIView):
    # DELETE → Delete all comments of a post. Only the post author is allowed.

    permission_classes = [IsAuthenticated]

    def delete(self, request, post_id):
        user = request.user
        post = get_object_or_404(Post, id=post_id)

        # Authorization: only post author
        if post.author != user:
            return Response(
                {"error": "Only the post author can delete all comments."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Count before deletion
        comments_qs = post.comments.all()
        total_comments = comments_qs.count()

        # Delete all
        comments_qs.delete()

        return Response(
            {
                "message": "All comments deleted successfully.",
                "deleted_comments_count": total_comments
            },
            status=status.HTTP_200_OK
        )