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

    def get_success_url(self):
        return reverse_lazy('pessoa:update', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super(PessoaUpdate, self).get_context_data(**kwargs)
        revalidar_form = ReValidarForm(prefix='revalidar', initial={'hash': self.object.pk, 'id': self.object.pk})
        deletar_form = DeletarForm(prefix='deletar', initial={'hash': self.object.pk, 'id': self.object.pk})

        context.update(
            {
                'revalidar_form': revalidar_form,
                'deletar_form': deletar_form
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        ret = super(PessoaUpdate, self).post(request, *args, **kwargs)

        revalidar_form = ReValidarForm(data=request.POST, prefix='revalidar', id_obj=self.object.pk)
        deletar_form = DeletarForm(data=request.POST, prefix='deletar', id_obj=self.object.pk)
        if revalidar_form:
            if revalidar_form.is_valid():
                messages.add_message(request, messages.INFO, 'revalidado')
                print('revalidado')
                return JsonResponse({
                    'mensagem': 'valido revalidado'
                })
            else:
                messages.add_message(request, messages.INFO, 'invalido revalidado')
                print('invalido  revalidado')

                return JsonResponse({
                    'mensagem': 'invalido revalidado'
                })

        if deletar_form:
            if deletar_form.is_valid():
                messages.add_message(request, messages.INFO, 'deletado')
                print('deletado')
                return JsonResponse({
                    'mensagem': 'valido deletado'
                })
            else:
                messages.add_message(request, messages.INFO, 'invalido deletado')
                print('invalido deletado')
                return JsonResponse({
                    'mensagem': 'invalido deletado'
                })

        return ret
