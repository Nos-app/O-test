from rest_framework import serializers
from .models import CityHistory

class CityHistorySerializer(serializers.ModelSerializer):
    count = serializers.IntegerField(read_only=True)

    class Meta:
        model = CityHistory
        fields = ('city', 'timestamp', 'count')
