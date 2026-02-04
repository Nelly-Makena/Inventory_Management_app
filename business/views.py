from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Business, Category, Supplier, Product,Sale
from .serializers import (
    BusinessSerializer,
    CategorySerializer,
    SupplierSerializer,
    ProductSerializer,
    SaleSerializer,

)
class BusinessProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            business = Business.objects.get(owner=request.user)
            serializer = BusinessSerializer(business)
            return Response(serializer.data)
        except Business.DoesNotExist:
            return Response({}, status=status.HTTP_200_OK)

    def post(self, request):
        business, created = Business.objects.get_or_create(
            owner=request.user
        )

        serializer = BusinessSerializer(
            business,
            data=request.data
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

class CategoryListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        business = request.user.business
        categories = Category.objects.filter(business=business)
        return Response(CategorySerializer(categories, many=True).data)

    def post(self, request):
        business = request.user.business
        serializer = CategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(business=business)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class SupplierListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        business = request.user.business
        suppliers = Supplier.objects.filter(business=business)
        return Response(SupplierSerializer(suppliers, many=True).data)

    def post(self, request):
        business = request.user.business
        serializer = SupplierSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(business=business)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProductCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        business = request.user.business
        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(business=business)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SaleCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SaleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)