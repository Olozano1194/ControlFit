from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..serializers.profile_serializer import UsuarioSerializer
from ..models import Usuario
from ..permissions import RequirePasswordChange


class userProfileView(APIView):
    permission_classes = [IsAuthenticated, RequirePasswordChange]

    def get(self, request):
        try:
            user_serializer = UsuarioSerializer(request.user, context={'request': request})
            user_data = user_serializer.data
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'user': user_data}, status=status.HTTP_200_OK)

    def list(self, request):
        try:
            gimnasio = request.gimnasio
            if gimnasio:
                users = Usuario.objects.filter(gimnasio=gimnasio).order_by('-id')
            else:
                users = Usuario.objects.none()
            serializer = UsuarioSerializer(users, many=True, context={'request': request})
            return Response({'users': serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)