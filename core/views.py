# Create your views here.
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


class PessoaCreate(BaseCreateUpdatePessoa, generic.CreateView):
    template_name = 'core/pessoa_update.html'


class PessoaUpdate(BaseCreateUpdatePessoa, generic.UpdateView):
    template_name = 'core/pessoa_update.html'

    def get_context_data(self, **kwargs):
        context = super(BaseCreateUpdatePessoa).get_context_data(**kwargs)
        revalidar_form = ReValidarForm(prefix='revalidar')
        deletar_form = DeletarForm(prefix='deletar')

        context.update(
            {
                'revalidar_form': revalidar_form,
                'deletar_form': deletar_form
            }
        )
