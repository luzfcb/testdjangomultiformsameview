# Create your views here.
from django.contrib import messages
from django.core.urlresolvers import reverse_lazy, reverse
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404, render
from django.utils import timezone
from django.views import generic
from .models import Pessoa, DocumentoLock
from .form import PessoaForm, ReValidarForm, DeletarForm
# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


class PessoaList(generic.ListView):
    model = Pessoa
    template_name = 'core/pessoa_list.html'


class PessoaDetail(generic.DetailView):
    model = Pessoa
    template_name = 'core/pessoa_detail.html'


class BaseCreateUpdatePessoa(object):
    model = Pessoa
    form_class = PessoaForm
    prefix = 'pessoa_update'


class PessoaCreate(generic.CreateView):
    model = Pessoa
    form_class = PessoaForm
    prefix = 'pessoa_create'
    template_name = 'core/pessoa_create.html'

    def get_success_url(self):
        return reverse_lazy('pessoa:update', kwargs={'pk': self.object.pk})


class DocumentoLockMixin(object):
    lock_expire_time_in_seconds = 30
    lock_revalidated_at_every_x_seconds = 5
    lock_revalidate_form_id = 'id_revalidar_form'
    lock_delete_form_id = 'id_deletar_form'
    lock_this_view_named_url_str = ''

    def create_lock(self, request, *args, **kwargs):
        if not self.object:
            self.object = self.get_object()

        with transaction.atomic():
            expira_em = timezone.now() + timezone.timedelta(seconds=self.lock_expire_time_in_seconds)
            label = get_label(self.object)

            documento_lock = DocumentoLock.objects.create(model_pk=self.object.pk,
                                                          app_and_model=label,
                                                          bloqueado_por=request.user,
                                                          bloqueado_por_user_name=request.user.username,
                                                          bloqueado_por_full_name=request.user.get_full_name(),
                                                          # session_key=session.session_key,
                                                          expire_date=expira_em)
            msg = 'Bloqueado documento: {} para {} '.format(documento_lock.model_pk,
                                                            documento_lock.bloqueado_por_full_name)
            logger.debug(msg)
            print(msg)

    def delete_lock(self, request, agora=timezone.now(), *args, **kwargs):
        if not self.object:
            self.object = self.get_object()
        with transaction.atomic():
            try:
                label = self.get_label(self.object)
                documento_lock = DocumentoLock.objects.get(model_pk=self.object.pk, app_and_model=label)
                if agora > documento_lock.expire_date:
                    documento_lock.delete()
                elif documento_lock.bloqueado_por.pk == request.user.pk:
                    documento_lock.delete()
                    msg = 'Deletado bloqueado documento: {} por {}'.format(documento_lock.model_pk,
                                                                           documento_lock.bloqueado_por_full_name)
                    print(msg)
                    logger.debug(msg)
            except DocumentoLock.DoesNotExist:
                logger.debug('Documento nao existe')
                print('Documento nao existe')

    def update_lock(self, request):
        if not self.object:
            self.object = self.get_object()
        with transaction.atomic():
            try:
                label = self.get_label(self.object)
                documento_lock = DocumentoLock.objects.get(model_pk=self.object.pk, app_and_model=label)

                if documento_lock.bloqueado_por.pk == request.user.pk:
                    expira_em = timezone.now() + timezone.timedelta(seconds=self.lock_expire_time_in_seconds)
                    documento_lock.expire_date = expira_em
                    documento_lock.save()
            except DocumentoLock.DoesNotExist:
                self.create_lock(request)

    def get(self, request, *args, **kwargs):
        original_response = super(DocumentoLockMixin, self).get(request, *args, **kwargs)
        # if self.object and self.object.esta_ativo:
        if self.object:
            try:
                label = self.get_label(self.object)
                documento_lock = DocumentoLock.objects.get(model_pk=self.object.pk, app_and_model=label)
                agora = timezone.now()
                if documento_lock and agora > documento_lock.expire_date:
                    self.delete_lock(request, agora)
                    # notificar o usuario DocumentoLock.bloqueado_por que ele perdeu o bloqueio
                    #
                    # trocar por um update
                    self.update_lock(request)
                    return original_response

                if documento_lock and not documento_lock.bloqueado_por.pk == request.user.pk:
                    detail_url = reverse('pessoa:detail', kwargs={'pk': self.object.pk})
                    msg = 'Documento está sendo editado por {} - Disponivel somente para visualização'.format(
                        documento_lock.bloqueado_por_full_name or documento_lock.bloqueado_por_user_name)
                    messages.add_message(request, messages.INFO, msg)
                    logger.debug(msg)
                    print(msg)
                    return redirect(detail_url, permanent=False)
            except DocumentoLock.DoesNotExist:
                self.create_lock(request)

        return original_response

    def post(self, request, *args, **kwargs):
        if request.is_ajax:
            if not hasattr(self, 'object'):

                self.object = self.get_object()
            else:
                if not self.object:
                    self.object = self.get_object()

            revalidar_form = ReValidarForm(data=request.POST,
                                           files=request.FILES,
                                           prefix='revalidar',
                                           id_obj=self.object.pk)
            deletar_form = DeletarForm(data=request.POST,
                                       files=request.FILES,
                                       prefix='deletar',
                                       id_obj=self.object.pk)

            if self.lock_revalidate_form_id in request.POST:
                if revalidar_form.is_valid():
                    self.update_lock(request)
                    print(revalidar_form.cleaned_data)
                    # messages.add_message(request, messages.INFO, 'revalidado com sucesso')
                    print('revalidado com sucesso')
                    return JsonResponse({
                        'mensagem': 'revalidado com sucesso',
                        'id': self.object.pk
                    })
                else:
                    messages.add_message(request, messages.INFO, 'erro ao revalidar')
                    print('erro ao revalidar')

                    return JsonResponse({
                        'mensagem': 'erro ao revalidar',
                        'id': self.object.pk
                    })

            if self.lock_delete_form_id in request.POST:
                if deletar_form.is_valid():
                    self.delete_lock(request)
                    print(deletar_form.cleaned_data)
                    # messages.add_message(request, messages.INFO, 'deletado com sucesso')
                    print('deletado com sucesso')
                    return JsonResponse({
                        'mensagem': 'deletado com sucesso',
                        'id': self.object.pk
                    })
                else:
                    messages.add_message(request, messages.INFO, 'erro ao deletar')
                    print('erro ao deletar')
                    return JsonResponse({
                        'mensagem': 'erro ao deletar',
                        'id': self.object.pk
                    })

        ret = super(DocumentoLockMixin, self).post(request, *args, **kwargs)

        return ret

    def get_context_data(self, **kwargs):
        context = super(DocumentoLockMixin, self).get_context_data(**kwargs)
        revalidate = 15

        if self.lock_revalidated_at_every_x_seconds and self.lock_revalidated_at_every_x_seconds <= self.lock_expire_time_in_seconds / 2:
            revalidate = self.lock_revalidated_at_every_x_seconds
        context.update({
            'revalidate_lock_at_every_x_seconds': revalidate
        })

        revalidar_form = ReValidarForm(prefix='revalidar', initial={'hash': self.object.pk, 'id': self.object.pk})
        deletar_form = DeletarForm(prefix='deletar', initial={'hash': self.object.pk, 'id': self.object.pk})

        context.update(
            {
                'revalidar_form': revalidar_form,
                'revalidar_form_id': self.lock_revalidate_form_id,
                'deletar_form': deletar_form,
                'deletar_form_id': self.lock_delete_form_id,
                'update_view_str': 'pessoa:update'
            }
        )
        return context


class PessoaUpdate(DocumentoLockMixin, generic.UpdateView):
    model = Pessoa
    form_class = PessoaForm
    prefix = 'pessoa_update'
    template_name = 'core/pessoa_update.html'

    def get_success_url(self):
        return reverse_lazy('pessoa:update', kwargs={'pk': self.object.pk})


###################################################################################################################
lock_expire_time_in_seconds = 30
lock_revalidated_at_every_x_seconds = 5
lock_revalidate_form_id = 'id_revalidar_form'
lock_delete_form_id = 'id_deletar_form'
lock_this_view_named_url_str = ''
update_view_str = 'pessoa:update2'
detail_view_str = 'pessoa:detail'


def create_lock(request, obj, *args, **kwargs):
    with transaction.atomic():
        expira_em = timezone.now() + timezone.timedelta(seconds=lock_expire_time_in_seconds)
        label = get_label(obj)

        documento_lock = DocumentoLock.objects.create(model_pk=obj.pk,
                                                      app_and_model=label,
                                                      bloqueado_por=request.user,
                                                      bloqueado_por_user_name=request.user.username,
                                                      bloqueado_por_full_name=request.user.get_full_name(),
                                                      # session_key=session.session_key,
                                                      expire_date=expira_em)
        msg = 'Bloqueado documento: {} para {} '.format(documento_lock.model_pk,
                                                        documento_lock.bloqueado_por_full_name)
        logger.debug(msg)
        print(msg)


def delete_lock(request, obj, agora=timezone.now(), *args, **kwargs):
    with transaction.atomic():
        try:
            label = get_label(obj)
            documento_lock = DocumentoLock.objects.get(model_pk=obj.pk, app_and_model=label)
            if agora > documento_lock.expire_date:
                documento_lock.delete()
            elif documento_lock.bloqueado_por.pk == request.user.pk:
                documento_lock.delete()
                msg = 'Deletado bloqueado documento: {} por {}'.format(documento_lock.model_pk,
                                                                       documento_lock.bloqueado_por_full_name)
                print(msg)
                logger.debug(msg)
        except DocumentoLock.DoesNotExist:
            logger.debug('Documento nao existe')
            print('Documento nao existe')


def update_lock(request, obj):
    with transaction.atomic():
        try:
            label = get_label(obj)
            documento_lock = DocumentoLock.objects.get(model_pk=obj.pk, app_and_model=label)

            if documento_lock.bloqueado_por.pk == request.user.pk:
                expira_em = timezone.now() + timezone.timedelta(seconds=lock_expire_time_in_seconds)
                documento_lock.expire_date = expira_em
                documento_lock.save()
        except DocumentoLock.DoesNotExist:
            create_lock(request, obj)


def get_label(model_instance):
    """
    :param model_instance:
    :return:
    """
    return '{app_name}.{model_name}'.format(app_name=model_instance._meta.app_label,
                                            model_name=str(model_instance.__class__.__name__).lower())


def update_view(request, pk):
    obj = get_object_or_404(Pessoa, pk=pk)

    if request.method == 'POST':
        pass
    else:
        # GET
        if obj:
            try:
                label = get_label(obj)
                documento_lock = DocumentoLock.objects.get(model_pk=obj.pk, app_and_model=label)
                agora = timezone.now()
                if documento_lock and agora > documento_lock.expire_date:
                    delete_lock(request, obj, agora)
                    # notificar o usuario DocumentoLock.bloqueado_por que ele perdeu o bloqueio
                    #
                    # trocar por um update
                    update_lock(request, obj)
                    return ''  # original_response

                if documento_lock and not documento_lock.bloqueado_por.pk == request.user.pk:
                    detail_url = reverse('pessoa:detail', kwargs={'pk': obj.pk})
                    msg = 'Documento está sendo editado por {} - Disponivel somente para visualização'.format(
                        documento_lock.bloqueado_por_full_name or documento_lock.bloqueado_por_user_name)
                    messages.add_message(request, messages.INFO, msg)
                    logger.debug(msg)
                    print(msg)
                    return redirect(detail_url, permanent=False)
            except DocumentoLock.DoesNotExist:
                create_lock(request, obj)

        revalidar_form = ReValidarForm(prefix='revalidar', initial={'hash': obj.pk, 'id': obj.pk})
        deletar_form = DeletarForm(prefix='deletar', initial={'hash': obj.pk, 'id': obj.pk})

        revalidate = None
        context = {}

        if lock_revalidated_at_every_x_seconds and lock_revalidated_at_every_x_seconds <= lock_expire_time_in_seconds / 2:
            revalidate = lock_revalidated_at_every_x_seconds

        context.update(
            {
                'revalidate_lock_at_every_x_seconds': revalidate,
                'revalidar_form': revalidar_form,
                'revalidar_form_id': lock_revalidate_form_id,
                'deletar_form': deletar_form,
                'deletar_form_id': lock_delete_form_id,
                'update_view_str': update_view_str,
                'object': obj,

            }
        )

        return render(request, 'core/pessoa_update.html', context=context)

