import datetime

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .models import Question, Choice

class QuestionModelTests(TestCase):
    def test_was_published_recently_with_future_question(self):
        """ was_published_recently() returns False for questions whose pub_date is in the future."""

        time = timezone.now() + datetime.timedelta(days = 30)
        future_question = Question(pub_date=time)
        self.assertIs(future_question.was_published_recently(), False)

    def test_was_published_recently_with_old_question(self):
        """
        was_published_recently() returns False for questions whose pub_date
        is older than 1 day.
        """
        time = timezone.now() - datetime.timedelta(days=1, seconds=1)
        old_question = Question(pub_date=time)
        self.assertIs(old_question.was_published_recently(), False)


    def test_was_published_recently_with_recent_question(self):
        """
        was_published_recently() returns True for questions whose pub_date
        is within the last day.
        """
        time = timezone.now() - datetime.timedelta(hours=23, minutes=59, seconds=59)
        recent_question = Question(pub_date=time)
        self.assertIs(recent_question.was_published_recently(), True)

    def test_create_question(self):
        question = create_question(question_text="Sample question.", days=-1)
        self.assertEqual(question.question_text, "Sample question.")
        self.assertLessEqual(question.pub_date, timezone.now())

    def test_create_question_with_choice(self):
        question = create_question(question_text="Sample question.", days=-1)
        choice = Choice.objects.create(question=question, choice_text="Sample choice.")
        self.assertEqual(choice.question, question)
        self.assertEqual(choice.choice_text, "Sample choice.")

    def test_create_question_with_multiple_choices(self):
        question = create_question(question_text="Sample question.", days=-1)
        choice1 = Choice.objects.create(question=question, choice_text="Sample choice 1.")
        choice2 = Choice.objects.create(question=question, choice_text="Sample choice 2.")
        self.assertEqual(choice1.question, question)
        self.assertEqual(choice1.choice_text, "Sample choice 1.")
        self.assertEqual(choice2.question, question)
        self.assertEqual(choice2.choice_text, "Sample choice 2.")

    def test_delete_question_with_no_choices(self):
        question = create_question(question_text="Sample question.", days=-1)
        question.delete()
        with self.assertRaises(Question.DoesNotExist):
            Question.objects.get(pk=question.pk)

    def test_delete_question_with_choice(self):
        question = create_question(question_text="Sample question.", days=-1)
        choice = Choice.objects.create(question=question, choice_text="Sample choice.")
        question.delete()
        with self.assertRaises(Question.DoesNotExist):
            Question.objects.get(pk=question.pk)
        with self.assertRaises(Choice.DoesNotExist):
            Choice.objects.get(pk=choice.pk)

    def test_delete_question_with_multiple_choices(self):
        question = create_question(question_text="Sample question.", days=-1)
        choice1 = Choice.objects.create(question=question, choice_text="Sample choice 1.")
        choice2 = Choice.objects.create(question=question, choice_text="Sample choice 2.")
        question.delete()
        with self.assertRaises(Question.DoesNotExist):
            Question.objects.get(pk=question.pk)
        with self.assertRaises(Choice.DoesNotExist):
            Choice.objects.get(pk=choice1.pk)
        with self.assertRaises(Choice.DoesNotExist):
            Choice.objects.get(pk=choice2.pk)

    def test_delete_choice(self):
        question = create_question(question_text="Sample question.", days=-1)
        choice = Choice.objects.create(question=question, choice_text="Sample choice.")
        choice.delete()
        with self.assertRaises(Choice.DoesNotExist):
            Choice.objects.get(pk=choice.pk)
        """check that question now have no choices left"""
        self.assertQuerySetEqual(question.choice_set.all(), [])

    def test_delete_choice_when_multiple_choices_exist(self):
        question = create_question(question_text="Sample question.", days=-1)
        choice1 = Choice.objects.create(question=question, choice_text="Sample choice 1.")
        choice2 = Choice.objects.create(question=question, choice_text="Sample choice 2.")
        choice1.delete()
        with self.assertRaises(Choice.DoesNotExist):
            Choice.objects.get(pk=choice1.pk)
        """check that question still has the remaining choice"""
        self.assertQuerySetEqual(question.choice_set.all(), [choice2])


    

class ChoiceModelTests(TestCase):
    def test_choice_creation(self):
        question = create_question(question_text="Sample question.", days=-1)
        choice = Choice.objects.create(question=question, choice_text="Sample choice.")
        self.assertEqual(choice.question, question)
        self.assertEqual(choice.choice_text, "Sample choice.")

    def test_choice_str(self):
        question = create_question(question_text="Sample question.", days=-1)
        choice = Choice.objects.create(question=question, choice_text="Sample choice.")
        self.assertEqual(str(choice), "Sample choice.")


def create_question(question_text, days):
    """
    Create a question with the given `question_text` and published the
    given number of `days` offset to now (negative for questions published
    in the past, positive for questions that have yet to be published).
    """
    time = timezone.now() + datetime.timedelta(days=days)
    return Question.objects.create(question_text=question_text, pub_date=time)

class QuestionIndexViewTests(TestCase):
    def test_no_questions(self):
        """
        If no questions exist, an appropriate message is displayed.
        """
        response = self.client.get(reverse("polls:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls are available.")
        self.assertQuerySetEqual(response.context["latest_question_list"], [])

    def test_past_question(self):
        """
        Questions with a pub_date in the past are displayed on the
        index page.
        """
        question = create_question(question_text="Past question.", days=-30)
        response = self.client.get(reverse("polls:index"))
        self.assertQuerySetEqual(
            response.context["latest_question_list"],
            [question],
        )

    def test_future_question(self):
        """
        Questions with a pub_date in the future aren't displayed on
        the index page.
        """
        create_question(question_text="Future question.", days=30)
        response = self.client.get(reverse("polls:index"))
        self.assertContains(response, "No polls are available.")
        self.assertQuerySetEqual(response.context["latest_question_list"], [])

    def test_future_question_and_past_question(self):
        """
        Even if both past and future questions exist, only past questions
        are displayed.
        """
        question = create_question(question_text="Past question.", days=-30)
        create_question(question_text="Future question.", days=30)
        response = self.client.get(reverse("polls:index"))
        self.assertQuerySetEqual(
            response.context["latest_question_list"],
            [question],
        )

    def test_two_past_questions(self):
        """
        The questions index page may display multiple questions.
        """
        question1 = create_question(question_text="Past question 1.", days=-30)
        question2 = create_question(question_text="Past question 2.", days=-5)
        response = self.client.get(reverse("polls:index"))
        self.assertQuerySetEqual(
            response.context["latest_question_list"],
            [question2, question1],
        )

class QuestionDetailViewTests(TestCase):
    def test_future_question(self):
        """
        The detail view of a question with a pub_date in the future returns a 404 not found.
        """
        future_question = create_question(question_text="Future question.", days=30)
        url = reverse("polls:detail", args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question(self):
        """
        The detail view of a question with a pub_date in the past displays the question's text.
        """
        past_question = create_question(question_text="Past question.", days=-30)
        url = reverse("polls:detail", args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)

class QuestionResultsViewTests(TestCase):
    def test_future_question(self):
        """
        The results view of a question with a pub_date in the future returns a 404 not found.
        """
        future_question = create_question(question_text="Future question.", days=30)
        url = reverse("polls:results", args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question(self):
        """
        The results view of a question with a pub_date in the past displays the question's text.
        """
        past_question = create_question(question_text="Past question.", days=-30)
        url = reverse("polls:results", args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)

class VoteViewTests(TestCase):
    def test_vote_on_future_question(self):
        """
        Voting on a question with a pub_date in the future returns a 404 not found.
        """
        future_question = create_question(question_text="Future question.", days=30)
        choice = Choice.objects.create(question=future_question, choice_text="Sample choice.")
        url = reverse("polls:vote", args=(future_question.id,))
        response = self.client.post(url, {"choice": choice.id})
        self.assertEqual(response.status_code, 404)

    def test_vote_on_past_question(self):
        """
        Voting on a question with a pub_date in the past redirects to the results page.
        """
        past_question = create_question(question_text="Past question.", days=-30)
        choice = Choice.objects.create(question=past_question, choice_text="Sample choice.")
        url = reverse("polls:vote", args=(past_question.id,))
        response = self.client.post(url, {"choice": choice.id})
        self.assertRedirects(response, reverse("polls:results", args=(past_question.id,)))

    def test_vote_without_selecting_choice(self):
        """
        Voting on a question without selecting a choice redisplays the question form with an error message.
        """
        past_question = create_question(question_text="Past question.", days=-30)
        Choice.objects.create(question=past_question, choice_text="Sample choice.")
        url = reverse("polls:vote", args=(past_question.id,))
        response = self.client.post(url, {})
        self.assertContains(response, "No choice selected.")
    
    def test_vote_on_nonexistent_choice(self):
        """
        Voting on a question with a choice that does not exist redisplays the question form with an error message.
        """
        past_question = create_question(question_text="Past question.", days=-30)
        Choice.objects.create(question=past_question, choice_text="Sample choice.")
        url = reverse("polls:vote", args=(past_question.id,))
        response = self.client.post(url, {"choice": 999})
        self.assertContains(response, "Choice does not exist.")

    def test_vote_on_question_without_choices(self):
        """
        Voting on a question that has no choices redisplays the question form with an error message.
        """
        past_question = create_question(question_text="Past question.", days=-30)
        url = reverse("polls:vote", args=(past_question.id,))
        response = self.client.post(url, {"choice": 1})
        self.assertContains(response, "Choice does not exist.")
    
    def test_vote_on_an_existing_choices(self):
        """
        Voting on a question with an existing choice increments the vote count and redirects to the results page.
        """
        past_question = create_question(question_text="Past question.", days=-30)
        choice = Choice.objects.create(question=past_question, choice_text="Sample choice.", votes = 5)
        url = reverse("polls:vote", args=(past_question.id,))
        response = self.client.post(url, {"choice": choice.id})
        self.assertRedirects(response, reverse("polls:results", args=(past_question.id,)))
        choice.refresh_from_db()
        self.assertEqual(choice.votes, 6)

