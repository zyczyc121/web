from .forms import LoginForm

def login_form(request):
    if request.method=='GET' and not request.user.is_authenticated():
        form = LoginForm()
        return {'login_form': form}
    else:
        return {}
