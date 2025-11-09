from django.contrib.auth.hashers import check_password
from home.models import Trainee

class TraineeAuthBackend:
    def authenticate(self, request, trainee_number=None, password=None):
        try:
            trainee = Trainee.objects.get(trainee_number=trainee_number)
            # Check if password matches trainee number or hashed password
            if password == trainee.trainee_number or trainee.check_password(password):
                return trainee
        except Trainee.DoesNotExist:
            return None
        return None
    
    def get_user(self, user_id):
        try:
            return Trainee.objects.get(pk=user_id)
        except Trainee.DoesNotExist:
            return None