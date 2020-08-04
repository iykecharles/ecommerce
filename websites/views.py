from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, View, CreateView, UpdateView, DeleteView
from .models import Item, OrderItem, Order, Address, UserProfile
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from .forms import CheckoutForm
import stripe

stripe.api_key = "sk_test_4eC39HqLyjWDarjtT1zdp7dc"


def is_valid_form(values):
    valid = True
    for field in values:
        if field == '':
            valid = False
    return valid


class HomeView(ListView):
    model = Item
    template_name = "home-page.html"
    paginate_by = 4


class ItemDetailView(DetailView):
    model = Item
    template_name = "product-page.html"


class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Item
    fields = ["title", "description", "price",
              "label", "category", "discount_price"]

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Item
    fields = ["title", "description", "price",
              "label", "category", "discount_price"]

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class ProductDeleteView(LoginRequiredMixin, DeleteView):
    model = Item
    success_url = "/"

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


@login_required
def add_to_cart(request, pk):
    item = get_object_or_404(Item, pk=pk)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False
    )
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item_id=item.pk).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, f"This item quantity was updated")
            return redirect("/order-summary/")
        else:
            order.items.add(order_item)
            messages.info(request, f"This item was added to your cart1")
            return redirect("/order-summary/")
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(
            user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, f"This item was added to your cart2")
        return redirect("/order-summary/")


@login_required
def remove_single_item_from_cart(request, pk):
    item = get_object_or_404(Item, pk=pk)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item_id=item.pk).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            messages.info(request, f"Your order has been updated")
            return redirect("/order-summary/")
        else:
            messages.info(request, f"You do not have a valid order")
            return redirect("/order-summary/")
    else:
        messages.info(request, f"You do not have a valid order")
        return redirect("/order-summary/")


@login_required
def remove_from_cart(request, pk):
    item = get_object_or_404(Item, pk=pk)

    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item_id=item.pk).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            order.items.remove(order_item)
            order_item.delete()
            messages.info(request, f"rrrrrrrrrrrrrrrrrrrrrrrrree")
            return redirect("/order-summary/")
        else:
            messages.info(request, f"This item was added to your cart1")
            return redirect("/order-summary/")
    else:
        messages.info(request, f"You do not have a valid order")
        return redirect("/order-summary/")


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                "object": order
            }
            return render(self.request, "websites/order_summary.html", context)
        except ObjectDoesNotExist:
            messages.info(request, f"You do not have a valid order")
            return redirect("/")


class CheckoutView(View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(
                user=self.request.user,
                ordered=False,
            )
            form = CheckoutForm()
            context = {
                "order": order,
                "form": form
            }
            shipping_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type="S",
                default=True
            )
            if shipping_address_qs.exists():
                context.update(
                    {"default_shipping_address": shipping_address_qs[0]}
                )
            billing_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type="B",
                default=True
            )
            if billing_address_qs.exists():
                context.update(
                    {"default_billing_address": billing_address_qs[0]}
                )
            return render(self.request, "checkout-page.html", context)
        except ObjectDoesNotExist:
            messages.info(
                self.request, f"There exist no default shipping information")
            return redirect("checkout")

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(
                user=self.request.user,
                ordered=False,
            )
            if form.is_valid():
                use_default_shipping = form.cleaned_data.get(
                    "use_default_shipping")
                if use_default_shipping:
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type="S",
                        default=True
                    )
                    if address_qs.exists():
                        shipping_address = address_qs[0]
                        order.shipping_address = shipping_address
                        order.save()

                    else:
                        messages.info(
                            self.request, f"There exist no default shipping information")
                        return redirect('checkout')
                else:
                    messages.info(
                        self.request, f"In the absence of default shipping information, new data would be used")
                    shipping_address1 = form.cleaned_data.get(
                        "shipping_address")
                    shipping_address2 = form.cleaned_data.get(
                        "shipping_address2")
                    shipping_country = form.cleaned_data.get(
                        "shipping_country")
                    shipping_zip = form.cleaned_data.get("shipping_zip")

                    if is_valid_form([shipping_address1, shipping_country, shipping_zip]):
                        shipping_address = Address(
                            user=self.request.user,
                            street_address=shipping_address1,
                            apartment_address=shipping_address2,
                            countries=shipping_country,
                            zip=shipping_zip,
                            address_type="S",
                        )
                        shipping_address.save()
                        order.shipping_address = shipping_address
                        order.save()

                        set_default_shipping = form.cleaned_data.get(
                            "set_default_shipping")
                        if set_default_shipping:
                            shipping_address.default = True
                            shipping_address.save()

                    else:
                        messages.info(
                            self.request, f"forms or data entered arent valid")

                use_default_billing = form.cleaned_data.get(
                    "use_default_billing")
                same_billing_address = form.cleaned_data.get(
                    "same_billing_address")

                if same_billing_address:
                    billing_address = shipping_address
                    billing_address.pk = None
                    billing_address.save()
                    billing_address.address_type = "B"
                    billing_address.save()
                    order.billing_address = billing_address
                    order.save()

                elif use_default_billing:
                    address_qs = Address.objects.filter(user=self.request.user,
                                                        address_type="B",
                                                        default=True
                                                        )

                    if address_qs.exists():
                        billing_address = address_qs[0]
                        order.billing_address = billing_address
                        order.save()

                    else:
                        messages.info(
                            self.request, f"There exist no default billing information")
                        return redirect("checkout")
                else:
                    messages.info(
                        self.request, f"In the absence of default billing information, new data would be used")
                    billing_address1 = form.cleaned_data.get("billing_address")
                    billing_address2 = form.cleaned_data.get(
                        "billing_address2")
                    billing_country = form.cleaned_data.get("billing_country")
                    billing_zip = form.cleaned_data.get("billing_zip")
                    if is_valid_form([billing_address1, billing_country, billing_zip]):
                        billing_address = Address(
                            user=self.request.user,
                            street_address=billing_address1,
                            apartment_address=billing_address2,
                            countries=billing_country,
                            zip=billing_zip,
                            address_type="B",
                        )
                        billing_address.save()
                        order.billing_address = billing_address
                        order.save()

                        set_default_billing = form.cleaned_data.get(
                            "set_default_billing")

                        if set_default_billing:
                            billing_address.default = True
                            billing_address.save()
                            order.billing_address = billing_address
                            order.save()
                    else:
                        messages.info(
                            self.request, f"There exist no default billing information")

                payment_option = form.cleaned_data.get("payment_option")
                if payment_option == "S":
                    return redirect("payment", payment_option="Stripe")
                elif payment_option == "P":
                    return redirect("payment", payment_option="paypal")
                else:
                    messages.info(
                        self.request, f"Please select a valid payment option")
                    return redirect("checkout")
        except ObjectDoesNotExist:
            messages.info(
                self.request, f"Please select a valid payment option")
            return redirect("order-summary")


class Payment(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        if order.billing_address:
            context = {"order": order}
            userprofile = self.request.user.userprofile
            if userprofile.one_click_purchasing:
                cards = stripe.Customer.list_sources(
                    userprofile.stripe_customer_id,
                    limit=3,
                    object='card'
                )
                card_list = card["data"]
                if len(card_list) > 0:
                    context.update({"card": card_list[0]})
            return render(self.request, "payment.html", context)
        else:
            messages.info(
                self.request, f"You do not have a valid billing address")
            return redirect("home")

    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        form = Payment(request.POST)
        userprofile = Userprofile.objects.get(
            user=self.request.user.userprofile)
        if form.is_valid():
            save = form.cleaned_data.get("save")
            stripeToken = form.cleaned_data.get("stripeToken")
            use_default = form.cleaned_data.get("use_default")
            if save:
                if userprofile.one_click_purchasing != "" and userprofile.one_click_purchasing is not None:
                    customer = stripe.Customer.retrieve(
                        stripe_customer_id
                    )
                    customer.source.create(source=Token)
                else:
                    customer = stripe.Customer.create(
                        email=user.request.user.email
                    )
                    customer.source.create(source=Token)
                    userprofile.stripe_customer_id = customer["id"]
                    userprofile.one_click_purchasing = True
                    userprofile.save()

            amount = int(order.get_total()*100)

            try:
                if use_default or save:
                    # charge the customer because we cannot charge the token more than once
                    charge = stripe.Charge.create(
                        amount=amount,  # cents
                        currency="usd",
                        customer=userprofile.stripe_customer_id
                    )
                else:
                    # charge once off on the token
                    charge = stripe.Charge.create(
                        amount=amount,  # cents
                        currency="usd",
                        source=token
                    )

                payment = Payment()
                payment.amount = order.get_total()
                payment.user = self.request.user
                payment.stripe_charge_id = charge["id"]
                payment.save()

                order.ordered = True
                order.payment = payment
                order.save()

                messages.warning(
                    self.request, f"rtepppppppppppppppppppppppppppppp")
                return redirect("/")

            except stripe.error.CardError as e:
                messages.warning(self.request, "CardError")
                return redirect("/")

            except stripe.error.RateLimitError as e:
                messages.warning(self.request, "RateLimitError")
                return redirect("/")

            except stripe.error.InvalidRequestError as e:
                messages.warning(self.request, "InvalidRequestError")
                return redirect("/")

            except stripe.error.AuthenticationError as e:
                messages.warning(self.request, "AuthenticationError")
                return redirect("/")

            except stripe.error.APIConnectionError as e:
                messages.warning(self.request, "Internet connection error")
                return redirect("/")

            except stripe.error.StripeError as e:
                messages.warning(self.request, "StripeError")
                return redirect("/")

            except Exception as e:
                messages.warning(self.request, "CardError")
                return redirect("/")

        return render(self.request, "payment.html")
