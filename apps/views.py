
import re

from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin

from django.db.models import F, Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, ListView, FormView, DetailView
import django.contrib.auth.password_validation as validators

from apps.forms import OrderForm, StreamForm
from apps.models import Category, Product, User, WishList, Order, Stream, Comment, SiteSettings


class CategoryListView(ListView):
    queryset = Product.objects.all().select_related('category')
    template_name = 'apps/trade/home-page.html'
    context_object_name = 'products'
    paginate_by = 3

    def get_context_data(self, **kwargs):
        data = super().get_context_data()
        data['categories'] = Category.objects.all()
        return data


class ProductListView(ListView):
    queryset = Product.objects.all().prefetch_related('images')
    template_name = 'apps/trade/product-list.html'
    context_object_name = 'products'

    def get_queryset(self):
        cat_slug = self.request.GET.get("category")
        query = super().get_queryset()
        if cat_slug:
            query = query.filter(category__slug=cat_slug)
        return query

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['categories'] = Category.objects.all()
        return data


class ProductDetailView(DetailView, FormView):
    form_class = OrderForm
    model = Product
    template_name = 'apps/trade/product-detail.html'
    context_object_name = 'product'

    def form_valid(self, form):
        if form.is_valid():
            form = form.save(commit=False)
            form.user = self.request.user
            form.save()
        return render(self.request, 'apps/order/product-order.html', {'form': form})


class CustomLoginView(TemplateView):
    template_name = 'apps/auth/login.html'

    def post(self, request, *args, **kwargs):
        phone_number = re.sub(r'\D', '', request.POST.get('phone_number'))
        user = User.objects.filter(phone_number=phone_number).first()
        if not user:
            # is_ = validators.validate_password(request.POST['PASSWORD'])

            user = User.objects.create_user(phone_number=phone_number, password=request.POST['password'])
            login(request, user)
            return redirect('home')
        else:
            user = authenticate(request, username=user.phone_number, password=request.POST['password'])
            if user:
                login(request, user)
                return redirect('home')

            else:
                context = {
                    "messages_error": ["Invalid password"]
                }
                return render(request, template_name='apps/auth/login.html', context=context)


class WishListView(LoginRequiredMixin, ListView):
    queryset = WishList.objects.all()
    template_name = 'apps/wish-list.html'
    paginate_by = 10
    context_object_name = "wishlists"

    def get_queryset(self):
        query = super().get_queryset().filter(user=self.request.user)
        return query


class LikeProductView(View):
    def post(self, request, *args, **kwargs):
        product = get_object_or_404(Product, slug=kwargs.get('slug'))
        obj, created = WishList.objects.get_or_create(user=request.user, product=product)
        if not created:
            obj.delete()
            return JsonResponse({'save': 0})
        return JsonResponse({'save': 1})


class OrderListView(ListView):
    queryset = Order.objects.all()
    template_name = 'apps/order/order-list.html'
    context_object_name = 'orders'

    def get_queryset(self):
        query = super().get_queryset().filter(user=self.request.user)
        return query


class MarketListView(ListView):
    template_name = 'apps/stream/product-market.html'
    queryset = Category.objects.all()
    context_object_name = 'categories'

    def get_context_data(self, *args, **kwargs):
        data = super().get_context_data(*args, **kwargs)
        products = Product.objects.all()
        if slug := self.request.GET.get("category"):
            products = products.filter(category__slug=slug)
        data['products'] = products
        return data


class StreamFormView(LoginRequiredMixin, FormView):
    form_class = StreamForm
    template_name = 'apps/stream/product-market.html'

    def form_valid(self, form):
        if form.is_valid():
            form.save()
        return redirect('stream-list')

    def form_invalid(self, form):
        print(form)


class StreamListView(ListView):
    queryset = Stream.objects.all()
    template_name = 'apps/stream/stream-list.html'
    context_object_name = 'streams'

    def get_queryset(self):
        return super().get_queryset().filter(owner=self.request.user)


class StreamDetailView(DetailView):
    queryset = Product.objects.all()
    template_name = 'apps/stream/stream-detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['self_stream'] = Stream.objects.filter(product= self.object , owner=self.request.user)
        return context



class StreamOrderView(DetailView , FormView):
    form_class = OrderForm
    queryset = Stream.objects.all()
    template_name = 'apps/trade/product-detail.html'
    context_object_name = 'stream'

    def form_valid(self, form):
        if form.is_valid():
            form = form.save(commit=False)
            form.stream = self.get_object()
            form.user = self.request.user
            form.save()
            form.product.price -= self.get_object().discount
            form.deliver_price = SiteSettings.objects.first().deliver_price
        return render(self.request, 'apps/order/product-order.html', {'form': form})

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data( **kwargs)
        product = self.object.product
        product.price -= self.object.discount
        context['product'] = product
        context['deliver_price'] = SiteSettings.objects.first().deliver_price
        stream_id = self.kwargs.get('pk')
        Stream.objects.filter(pk = stream_id).update(count= F('count') + 1)
        return context


class StreamStatisticsListView(ListView):
    queryset = Stream.objects.all()
    template_name = 'apps/stream/stream-statistics.html'
    context_object_name = 'streams'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query =self.get_queryset().aggregate(
            all_count = Sum('count'),
            all_new = Sum('new_count'),
            all_ready = Sum('ready_count'),
            all_deliver = Sum('deliver_count'),
            all_delivered = Sum('delivered_count'),
            all_cant_phone = Sum('cant_phone_count'),
            all_canceled = Sum('canceled_count'),
            all_archived = Sum('archived_count'),
        )
        context.update(query)
        return context

    def get_queryset(self):
        query = super().get_queryset().filter(owner=self.request.user).annotate(
            new_count=Count('orders', filter=Q(orders__status = Order.StatusType.NEW )),
            ready_count=Count('orders', filter=Q(orders__status = Order.StatusType.READY )),
            deliver_count=Count('orders', filter=Q(orders__status = Order.StatusType.DELIVER )),
            delivered_count=Count('orders', filter=Q(orders__status = Order.StatusType.DELIVERED )),
            cant_phone_count=Count('orders', filter=Q(orders__status = Order.StatusType.CANT_PHONE )),
            canceled_count=Count('orders', filter=Q(orders__status = Order.StatusType.CANCELED )),
            archived_count=Count('orders', filter=Q(orders__status = Order.StatusType.ARCHIVED )),
        ).values('name' , 'product__name' , 'count', 'new_count' ,
                 'ready_count',
                 'deliver_count',
                 'delivered_count',
                 'cant_phone_count',
                 'canceled_count',
                 'archived_count')
        return query
