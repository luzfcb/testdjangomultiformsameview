# Create your views here.
from django.contrib import messages
from django.core.urlresolvers import reverse_lazy
from django.http import JsonResponse
from django.views import generic
from .models import Pessoa
from .form import PessoaForm, ReValidarForm, DeletarForm


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
        ret = super(PessoaUpdate, self).post(request, *args, **kwargs)

        revalidar_form = ReValidarForm(data=request.POST,
                                       files=request.FILES,
                                       prefix='revalidar',
                                       id_obj=self.object.pk)
        deletar_form = DeletarForm(data=request.POST,
                                   files=request.FILES,
                                   prefix='deletar',
                                   id_obj=self.object.pk)
        print(request.POST)
        if self.revalidar_form_id in request.POST:
            if revalidar_form.is_valid():
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

        return ret
