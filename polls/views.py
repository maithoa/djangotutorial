from django.utils import timezone
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.http import Http404
from django.urls import reverse
from django.db.models import F
from django.views import generic
from .models import Choice, Question


class IndexView(generic.ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self):
        return Question.objects.filter(pub_date__lte=timezone.now()).order_by('-pub_date')[:5]

class DetailView(generic.DetailView):
    template_name = "polls/detail.html"
    def get_queryset(self):
        return Question.objects.filter(pub_date__lte=timezone.now())
    
class ResultsView(generic.DetailView):
    template_name = "polls/results.html"
    def get_queryset(self):
        return Question.objects.filter(pub_date__lte=timezone.now())  

def vote(request, question_id):
    """Record a vote for a published question."""
    question = get_object_or_404(Question, pk=question_id)

    if question.pub_date > timezone.now():
        raise Http404("Cannot vote on future questions.")

    choice_id = request.POST.get("choice")
    if not choice_id:
        return render(
            request,
            "polls/detail.html",
            {
                "question": question,
                "error_message": "No choice selected.",
            },
        )

    try:
        selected_choice = question.choice_set.get(pk=choice_id)
    except (Choice.DoesNotExist, ValueError):
        return render(
            request,
            "polls/detail.html",
            {
                "question": question,
                "error_message": "Choice does not exist.",
            },
        )

    selected_choice.votes = F("votes") + 1
    selected_choice.save()
    return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))


