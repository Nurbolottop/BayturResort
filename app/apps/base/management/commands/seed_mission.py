"""
Демо-наполнение блока «Миссия и цели» на странице «О нас».

Формулировки предварительные — их должен утвердить Заказчик.
Правится в админке: Страницы → Миссия и цели.
"""

from django.core.management.base import BaseCommand

from apps.cms.models import Mission, MissionGoal

MISSION = {
    'eyebrow': ('Наш замысел', 'Our idea', 'Биздин ой-максат'),
    'title': ('Миссия и цели', 'Mission and Goals', 'Миссия жана максаттар'),
    'statement': (
        'Мы создаём на Иссык-Куле место, куда возвращаются семьями: '
        'сервис уровня международного курорта и кыргызское гостеприимство, '
        'которое чувствуешь с первой минуты.',
        'We are building a place on Issyk-Kul that families come back to: '
        'international resort standards paired with Kyrgyz hospitality you '
        'feel from the first minute.',
        'Биз Ысык-Көлдө үй-бүлөлөр кайра келгиси келген жайды түзөбүз: '
        'эл аралык деңгээлдеги тейлөө жана биринчи мүнөттөн сезилген '
        'кыргыз конокжайлуулугу.',
    ),
    'content': (
        '<p>Baytur Resort &amp; Spa — премиальный семейный курорт на северном '
        'берегу Иссык-Куля, в селе Бостери. Мы объединили современную '
        'инфраструктуру с национальным колоритом: юрточный городок, '
        'кыргызская кухня и традиции соседствуют со SPA, бассейнами и '
        'конференц-залами.</p>',
        '<p>Baytur Resort &amp; Spa is a premium family resort on the northern '
        'shore of Issyk-Kul, in the village of Bosteri. We combine modern '
        'facilities with national character: a yurt camp, Kyrgyz cuisine and '
        'traditions alongside a spa, pools and conference halls.</p>',
        '<p>Baytur Resort &amp; Spa — Ысык-Көлдүн түндүк жээгиндеги, Бостери '
        'айылындагы премиум үй-бүлөлүк курорт. Биз заманбап инфраструктураны '
        'улуттук колорит менен айкалыштырдык: боз үй шаарчасы, кыргыз ашканасы '
        'жана салттар SPA, бассейндер жана конференц-залдар менен катар.</p>',
    ),
}

GOALS = [
    (
        ('Отдых для всей семьи', 'A holiday for the whole family', 'Бүт үй-бүлө үчүн эс алуу'),
        ('Продумываем территорию так, чтобы своё занятие нашлось у каждого — '
         'от малышей до старшего поколения.',
         'We design the grounds so that everyone finds something to do — '
         'from toddlers to grandparents.',
         'Аймакты ар ким өзүнө иш табышы үчүн ойлоштурабыз — '
         'наристелерден улуу муунга чейин.'),
    ),
    (
        ('Сервис без формальностей', 'Service without formality', 'Расмиятсыз тейлөө'),
        ('Обучаем команду встречать гостя как дома: внимательно, '
         'но без навязчивости.',
         'We train our team to welcome guests as if at home: attentive, '
         'never intrusive.',
         'Командабызды конокту үйдөгүдөй тосуп алууга үйрөтөбүз: '
         'кунт коюп, бирок тажатпай.'),
    ),
    (
        ('Кыргызстан, который запоминают', 'A Kyrgyzstan guests remember', 'Эсте каларлык Кыргызстан'),
        ('Показываем гостям культуру страны — через юрточный городок, '
         'кухню и национальные традиции.',
         'We show guests the country’s culture — through the yurt camp, '
         'the cuisine and national traditions.',
         'Конокторго өлкөнүн маданиятын көрсөтөбүз — боз үй шаарчасы, '
         'ашкана жана улуттук салттар аркылуу.'),
    ),
    (
        ('Бережное отношение к озеру', 'Care for the lake', 'Көлгө камкордук'),
        ('Следим за чистотой пляжа и территории: Иссык-Куль — причина, '
         'по которой к нам едут.',
         'We keep the beach and grounds clean: Issyk-Kul is the reason '
         'guests come to us.',
         'Жээктин жана аймактын тазалыгын карайбыз: Ысык-Көл — '
         'бизге келүүнүн себеби.'),
    ),
]


class Command(BaseCommand):
    help = 'Наполняет блок «Миссия и цели» демо-текстом (ru/en/ky).'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true',
                            help='Перезаписать уже заполненные тексты')

    def handle(self, *args, **options):
        force = options['force']
        mission = Mission.get_solo()

        for field, values in MISSION.items():
            for lang, value in zip(('ru', 'en', 'ky'), values):
                attr = '%s_%s' % (field, lang)
                if getattr(mission, attr, None) and not force:
                    continue
                setattr(mission, attr, value)
        mission.is_active = True
        mission.save()

        if mission.goals.exists() and not force:
            self.stdout.write('Цели уже заданы — пропускаю.')
        else:
            mission.goals.all().delete()
            for order, (titles, texts) in enumerate(GOALS):
                goal = MissionGoal(mission=mission, order=order)
                for lang, title, text in zip(('ru', 'en', 'ky'), titles, texts):
                    setattr(goal, 'title_%s' % lang, title)
                    setattr(goal, 'description_%s' % lang, text)
                goal.save()

        self.stdout.write(self.style.SUCCESS(
            'Блок «Миссия и цели» заполнен: целей — %s.' % mission.goals.count()
        ))
        self.stdout.write('Формулировки предварительные — заказчик правит их в админке.')
