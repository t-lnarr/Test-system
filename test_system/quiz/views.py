from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .models import Test, Question, Result, Profile
import random
from django.contrib.auth.models import User  # Bu satırı ekle
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def index(request):
    return render(request, 'index.html')

def student_login(request):
    if request.method == 'POST':
        request.session['student_name'] = request.POST['name']
        request.session['class_name'] = request.POST['class']
        return redirect('student_dashboard')
    return render(request, 'student_login.html')

def search_test(request):
    if request.method == 'POST':
        test_code = request.POST['test_code']
        try:
            test = Test.objects.get(test_code=test_code)
            return redirect('solve_test', test_code=test_code)
        except Test.DoesNotExist:
            return render(request, 'search_test.html', {'error': 'Test bulunamadı!'})
    return render(request, 'search_test.html')

def solve_test(request, test_code):
    test = Test.objects.get(test_code=test_code)
    questions = list(test.question_set.all())
    random.shuffle(questions)
    session_key = f'start_time_{test_code}'

    if request.method == 'POST':
        score = 0
        correct_answers = []
        incorrect_answers = []
        for question in questions:
            user_answer = request.POST.get(f'question_{question.id}')
            if user_answer == question.correct_answer:
                score += 1
                correct_answers.append({'text': question.text, 'answer': user_answer})
            else:
                incorrect_answers.append({'text': question.text, 'user_answer': user_answer, 'correct_answer': question.correct_answer})
        total = len(questions)
        percentage = (score / total * 100) if total > 0 else 0

        # Süreyi hesapla
        start_time = request.session.get(session_key)
        if start_time:
            start_dt = timezone.datetime.fromisoformat(start_time)
            end_dt = timezone.now()
            duration_seconds = (end_dt - start_dt).total_seconds()
            duration_minutes = duration_seconds / 60
        else:
            duration_minutes = None

        Result.objects.create(
            student_name=request.session['student_name'],
            class_name=request.session['class_name'],
            test=test,
            score=score,
            duration_minutes=duration_minutes
        )
        if session_key in request.session:
            del request.session[session_key]
        return render(request, 'result.html', {
            'score': score,
            'total': total,
            'percentage': percentage,
            'correct_answers': correct_answers,
            'incorrect_answers': incorrect_answers
        })

    if session_key not in request.session:
        request.session[session_key] = timezone.now().isoformat()
    start_time = request.session[session_key]
    time_limit = test.time_limit * 60

    return render(request, 'solve_test.html', {
        'test': test,
        'questions': questions,
        'time_limit': time_limit,
        'start_time': start_time
    })

def teacher_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Profil yoksa oluştur
            if not hasattr(user, 'profile'):
                Profile.objects.create(user=user, is_teacher=True)
            elif not user.profile.is_teacher:
                user.profile.is_teacher = True
                user.profile.save()
            return redirect('teacher_dashboard')
        else:
            return render(request, 'teacher_login.html', {'error': 'Ýalňyş ulanyjy ady ýa-da parol!'})
    return render(request, 'teacher_login.html')

@login_required
def teacher_dashboard(request):
    if not hasattr(request.user, 'profile') or not request.user.profile.is_teacher:
        return redirect('index')
    tests = Test.objects.filter(teacher=request.user)
    return render(request, 'teacher_dashboard.html', {'tests': tests})

def student_dashboard(request):
    if 'student_name' not in request.session:
        return redirect('student_login')
    tests = Test.objects.all()

    # Arama filtresi
    search_query = request.GET.get('search', '')
    if search_query:
        tests = tests.filter(test_code__icontains=search_query)

    if request.method == 'POST':
        test_code = request.POST['test_code']
        return redirect('solve_test', test_code=test_code)
    return render(request, 'student_dashboard.html', {'tests': tests, 'search_query': search_query})


@login_required
def create_test(request):
    if request.method == 'POST':
        if 'test_code' in request.POST and 'question_count' in request.POST:
            test_code = request.POST['test_code']
            question_count = int(request.POST['question_count'])
            time_limit = request.POST['time_limit']

            # Test kodu zaten varsa hata göster
            if Test.objects.filter(test_code=test_code).exists():
                return render(request, 'create_test.html', {
                    'error': f"'{test_code}' kody bilen test eýýäm bar. Başga bir kod saýlaň."
                })

            # Testi geçici olarak session’a kaydet
            request.session['pending_test'] = {
                'test_code': test_code,
                'question_count': question_count,
                'time_limit': time_limit
            }
            return render(request, 'create_questions.html', {'question_count': question_count})

        elif 'questions' in request.POST:
            pending_test = request.session.get('pending_test')
            if not pending_test:
                return redirect('teacher_dashboard')

            # Testi oluştur
            test = Test.objects.create(
                teacher=request.user,
                test_code=pending_test['test_code'],
                time_limit=pending_test['time_limit']
            )

            # Soruları kaydet
            for i in range(pending_test['question_count']):
                text = request.POST.get(f'question_text_{i}')
                options = {
                    'A': request.POST.get(f'opt_a_{i}'),
                    'B': request.POST.get(f'opt_b_{i}'),
                    'C': request.POST.get(f'opt_c_{i}'),
                    'D': request.POST.get(f'opt_d_{i}')
                }
                correct_answer = request.POST.get(f'correct_answer_{i}')
                Question.objects.create(
                    test=test,
                    text=text,
                    options=options,
                    correct_answer=correct_answer
                )
            del request.session['pending_test']
            return redirect('teacher_dashboard')

    return render(request, 'create_test.html')

@login_required
def test_detail(request, test_code):
    test = Test.objects.get(test_code=test_code, teacher=request.user)
    results = Result.objects.filter(test=test)
    questions = test.question_set.all()

    if request.method == 'POST':
        test.test_code = request.POST['test_code']
        test.time_limit = request.POST['time_limit']
        test.save()
        for question in questions:
            question.text = request.POST.get(f'question_text_{question.id}')
            question.options = {
                'A': request.POST.get(f'opt_a_{question.id}'),
                'B': request.POST.get(f'opt_b_{question.id}'),
                'C': request.POST.get(f'opt_c_{question.id}'),
                'D': request.POST.get(f'opt_d_{question.id}')
            }
            question.correct_answer = request.POST.get(f'correct_answer_{question.id}')
            question.save()
        return redirect('teacher_dashboard')

    class_stats = {}
    for result in results:
        class_name = result.class_name
        if class_name not in class_stats:
            class_stats[class_name] = {'total': 0, 'score_sum': 0}
        class_stats[class_name]['total'] += 1
        class_stats[class_name]['score_sum'] += result.score
    for class_name in class_stats:
        stats = class_stats[class_name]
        stats['average'] = stats['score_sum'] / stats['total'] if stats['total'] > 0 else 0

    return render(request, 'test_detail.html', {
        'test': test,
        'questions': questions,
        'results': results,
        'class_stats': class_stats
    })


@login_required
def dashboard(request):
    if not request.user.is_superuser:
        return redirect('index')
    teachers = User.objects.filter(profile__is_teacher=True)
    students = Result.objects.values('student_name', 'class_name').distinct()
    tests = Test.objects.all()
    results = Result.objects.all()

    class_stats = {}
    for result in results:
        class_name = result.class_name
        if class_name not in class_stats:
            class_stats[class_name] = {'total': 0, 'score_sum': 0, 'duration_sum': 0}
        class_stats[class_name]['total'] += 1
        class_stats[class_name]['score_sum'] += result.score
        if result.duration_minutes:
            class_stats[class_name]['duration_sum'] += result.duration_minutes
    for class_name in class_stats:
        stats = class_stats[class_name]
        stats['average_score'] = stats['score_sum'] / stats['total'] if stats['total'] > 0 else 0
        stats['average_duration'] = stats['duration_sum'] / stats['total'] if stats['total'] > 0 and stats['duration_sum'] > 0 else 0

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = User.objects.create_user(username=username, password=password)
        Profile.objects.create(user=user, is_teacher=True)
        return redirect('dashboard')

    return render(request, 'dashboard.html', {
        'teachers': teachers,
        'students': students,
        'tests': tests,
        'results': results,
        'class_stats': class_stats
    })
