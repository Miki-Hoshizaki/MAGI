from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .serializers import UserSerializer, UserCreateSerializer, UserProfileSerializer
from .models import UserProfile

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing user instances.
    """
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ['create', 'reset_password']:
            return [permissions.AllowAny()]
        return super().get_permissions()

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's profile."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def reset_password(self, request):
        """Initiate password reset process."""
        email = request.data.get('email')
        if not email:
            return Response(
                {'error': 'Email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email=email)
            # Here you would typically:
            # 1. Generate a password reset token
            # 2. Send an email with reset instructions
            # 3. Save the token in the database
            # For now, we'll just return a success message
            return Response({
                'message': 'Password reset instructions have been sent to your email.'
            })
        except User.DoesNotExist:
            return Response(
                {'error': 'User with this email does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def verify_email(self, request, pk=None):
        """Verify user's email address."""
        user = self.get_object()
        token = request.data.get('token')
        
        # Here you would typically:
        # 1. Validate the verification token
        # 2. Mark the user as verified
        # For now, we'll just mark the user as verified
        user.is_verified = True
        user.save()
        
        return Response({
            'message': 'Email verified successfully'
        })


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing user profile instances.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['patch'])
    def update_preferences(self, request):
        """Update user's notification preferences."""
        profile = self.get_queryset().first()
        if not profile:
            return Response(
                {'error': 'Profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        preferences = request.data.get('preferences', {})
        profile.notification_preferences.update(preferences)
        profile.save()
        
        return Response(UserProfileSerializer(profile).data) 