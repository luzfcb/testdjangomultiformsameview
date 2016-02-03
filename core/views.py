# Create your views here.
from django.contrib import messages
from django.core.urlresolvers import reverse_lazy, reverse
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect
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


class DocumentoLockMixin(generic.UpdateView):
    expire_time_in_seconds = 30
    revalidate_lock_at_every_x_seconds = 15
    revalidar_form_id = 'id_revalidar_form'
    deletar_form_id = 'id_deletar_form'

    def create_lock(self, request, *args, **kwargs):
        from django.contrib.sessions.models import Session
        # session = Session.objects.get(session_key=request.session.session_key)
        if not self.object:
            self.object = self.get_object()

        with transaction.atomic():
            expira_em = timezone.now() + timezone.timedelta(seconds=self.expire_time_in_seconds)

            documento_lock = DocumentoLock.objects.create(documento=self.object,
                                                          bloqueado_por=request.user,
                                                          bloqueado_por_user_name=request.user.username,
                                                          bloqueado_por_full_name=request.user.get_full_name(),
                                                          # session_key=session.session_key,
                                                          expire_date=expira_em)
            msg = 'Bloqueado documento: {}'.format(documento_lock.documento.pk)
            logger.debug(msg)
            print(msg)

    def delete_lock(self, request, agora=timezone.now(), *args, **kwargs):
        if not self.object:
            self.object = self.get_object()
        with transaction.atomic():
            try:
                documento_lock = DocumentoLock.objects.get(documento=self.object)
                if agora > documento_lock.expire_date:
                    documento_lock.delete()
                elif documento_lock.bloqueado_por.pk == request.user.pk:
                    documento_lock.delete()
                    msg = 'Deletado bloqueado documento: {}'.format(documento_lock.documento.pk)
                    print(msg)
                    logger.debug(msg)
            except DocumentoLock.DoesNotExist:
                logger.debug('Documento nao existe')
                print('Documento nao existe')

    def update_lock(self, request):
        if not self.object:
            self.object = self.get_object()
        with transaction.atomic():
            documento_lock = DocumentoLock.objects.get(documento=self.object)

            if documento_lock.bloqueado_por.pk == request.user.pk:
                expira_em = timezone.now() + timezone.timedelta(seconds=self.expire_time_in_seconds)
                documento_lock.expire_date = expira_em
                documento_lock.save()

    def get(self, request, *args, **kwargs):
        original_response = super(DocumentoLockMixin, self).get(request, *args, **kwargs)
        # if self.object and self.object.esta_ativo:
        if self.object:
            try:
                documento_lock = DocumentoLock.objects.get(documento=self.object)
                agora = timezone.now()
                if documento_lock and agora > documento_lock.expire_date:
                    self.delete_lock(request, agora)
                    # notificar o usuario DocumentoLock.bloqueado_por que ele perdeu o bloqueio
                    #
                    # trocar por um update
                    self.create_lock(request)
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

            if self.revalidar_form_id in request.POST:
                if revalidar_form.is_valid():
                    self.update_lock(request)
                    print(revalidar_form.cleaned_data)
                    # messages.add_message(request, messages.INFO, 'revalidado com sucesso')
                    print('revalidado com sucesso')
                    return JsonResponse({
                        'mensagem': 'revalidado com sucesso'
                    })
                else:
                    messages.add_message(request, messages.INFO, 'erro ao revalidar')
                    print('erro ao revalidar')

                    return JsonResponse({
                        'mensagem': 'erro ao revalidar'
                    })

            if self.deletar_form_id in request.POST:
                if deletar_form.is_valid():
                    self.delete_lock(request)
                    print(deletar_form.cleaned_data)
                    # messages.add_message(request, messages.INFO, 'deletado com sucesso')
                    print('deletado com sucesso')
                    return JsonResponse({
                        'mensagem': 'deletado com sucesso'
                    })
                else:
                    messages.add_message(request, messages.INFO, 'erro ao deletar')
                    print('erro ao deletar')
                    return JsonResponse({
                        'mensagem': 'erro ao deletar'
                    })

        ret = super(DocumentoLockMixin, self).post(request, *args, **kwargs)

        return ret

    def get_context_data(self, **kwargs):
        context = super(DocumentoLockMixin, self).get_context_data(**kwargs)
        revalidate = 15

        if self.revalidate_lock_at_every_x_seconds and self.revalidate_lock_at_every_x_seconds <= self.expire_time_in_seconds / 2:
            revalidate = self.revalidate_lock_at_every_x_seconds
        context.update({
            'revalidate_lock_at_every_x_seconds': revalidate
        })

        revalidar_form = ReValidarForm(prefix='revalidar', initial={'hash': self.object.pk, 'id': self.object.pk})
        deletar_form = DeletarForm(prefix='deletar', initial={'hash': self.object.pk, 'id': self.object.pk})

        context.update(
            {
                'revalidar_form': revalidar_form,
                'revalidar_form_id': self.revalidar_form_id,
                'deletar_form': deletar_form,
                'deletar_form_id': self.deletar_form_id
            }
        )
        return context


class PessoaUpdate(generic.UpdateView):
    model = Pessoa
    form_class = PessoaForm
    prefix = 'pessoa_update'
    template_name = 'core/pessoa_update.html'
    revalidar_form_id = 'id_revalidar_form'
    deletar_form_id = 'id_deletar_form'

    def get_success_url(self):
        return reverse_lazy('pessoa:update', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super(PessoaUpdate, self).get_context_data(**kwargs)
        revalidar_form = ReValidarForm(prefix='revalidar', initial={'hash': self.object.pk, 'id': self.object.pk})
        deletar_form = DeletarForm(prefix='deletar', initial={'hash': self.object.pk, 'id': self.object.pk})

        context.update(
            {
                'revalidar_form': revalidar_form,
                'revalidar_form_id': self.revalidar_form_id,
                'deletar_form': deletar_form,
                'deletar_form_id': self.deletar_form_id
            }
        )
        return context

    def post(self, request, *args, **kwargs):

        if request.is_ajax:
            self.object = self.get_object()

            revalidar_form = ReValidarForm(data=request.POST,
                                           files=request.FILES,
                                           prefix='revalidar',
                                           id_obj=self.object.pk)
            deletar_form = DeletarForm(data=request.POST,
                                       files=request.FILES,
                                       prefix='deletar',
                                       id_obj=self.object.pk)

            if self.revalidar_form_id in request.POST:
                if revalidar_form.is_valid():
                    print(revalidar_form.cleaned_data)
                    # messages.add_message(request, messages.INFO, 'revalidado com sucesso')
                    print('revalidado com sucesso')
                    return JsonResponse({
                        'mensagem': 'revalidado com sucesso'
                    })
                else:
                    messages.add_message(request, messages.INFO, 'erro ao revalidar')
                    print('erro ao revalidar')

                    return JsonResponse({
                        'mensagem': 'erro ao revalidar'
                    })

            if self.deletar_form_id in request.POST:
                if deletar_form.is_valid():
                    print(deletar_form.cleaned_data)
                    # messages.add_message(request, messages.INFO, 'deletado com sucesso')
                    print('deletado com sucesso')
                    return JsonResponse({
                        'mensagem': 'deletado com sucesso'
                    })
                else:
                    messages.add_message(request, messages.INFO, 'erro ao deletar')
                    print('erro ao deletar')
                    return JsonResponse({
                        'mensagem': 'erro ao deletar'
                    })
        ret = super(PessoaUpdate, self).post(request, *args, **kwargs)
        return ret
