/* =========================================================================
   Baytur Resort & Spa — фронтенд без внешних библиотек.
   ========================================================================= */

(function () {
    'use strict';

    var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // ------------------------------------------------------- мобильное меню
    var burger = document.querySelector('[data-burger]');
    var nav = document.querySelector('[data-nav]');

    if (burger && nav) {
        burger.addEventListener('click', function () {
            var open = nav.classList.toggle('is-open');
            burger.classList.toggle('is-open', open);
            burger.setAttribute('aria-expanded', open ? 'true' : 'false');
        });

        // Клик вне меню закрывает его
        document.addEventListener('click', function (event) {
            if (!nav.contains(event.target) && !burger.contains(event.target)) {
                nav.classList.remove('is-open');
                burger.classList.remove('is-open');
            }
        });
    }

    // ------------------------------------------- шапка: сжатие при прокрутке
    var header = document.querySelector('[data-header]');
    if (header) {
        var ticking = false;
        var onScroll = function () {
            header.classList.toggle('is-scrolled', window.pageYOffset > 40);
            ticking = false;
        };
        window.addEventListener('scroll', function () {
            if (!ticking) { window.requestAnimationFrame(onScroll); ticking = true; }
        }, { passive: true });
        onScroll();
    }

    // ------------------------------------------------ появление при скролле
    // Разметку не трогаем: элементы для анимации выбираются здесь, чтобы
    // шаблоны оставались чистыми.
    var revealSelector = [
        '.section__head', '.card', '.tile', '.advantage', '.review',
        '.result', '.form-card', '.detail__gallery', '.detail__aside',
        '.summary', '.embed', '.gallery-grid a', '.filters',
        '.booking-widget--inline', '.cta__inner', '.prose', '.specs', '.amenities',
    ].join(',');

    var revealTargets = Array.prototype.slice.call(document.querySelectorAll(revealSelector));

    if (reduceMotion || !('IntersectionObserver' in window)) {
        revealTargets.forEach(function (el) { el.classList.add('is-visible'); });
    } else {
        // Задержка внутри одного контейнера — эффект «набегания» карточек.
        // Ключ — сам DOM-узел, поэтому Map, а не объект: у объекта все
        // родители схлопнулись бы в одну строку "[object HTMLDivElement]".
        var groups = new Map();
        revealTargets.forEach(function (el) {
            el.setAttribute('data-reveal', '');
            var parent = el.parentNode;
            if (!groups.has(parent)) { groups.set(parent, []); }
            groups.get(parent).push(el);
        });

        groups.forEach(function (items) {
            items.forEach(function (el, index) {
                el.style.setProperty('--reveal-delay', Math.min(index, 5) * 90 + 'ms');
            });
        });

        var observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-visible');
                    observer.unobserve(entry.target);
                }
            });
        }, { rootMargin: '0px 0px -8% 0px', threshold: 0.06 });

        revealTargets.forEach(function (el) { observer.observe(el); });
    }

    // ------------------------------------------------------ слайдер на главной
    var slider = document.querySelector('[data-slider]');
    if (slider) {
        var slides = slider.querySelectorAll('[data-slide]');
        var dots = slider.querySelectorAll('[data-slide-to]');
        var current = 0;
        var timer = null;

        function show(index) {
            if (!slides.length) return;
            current = (index + slides.length) % slides.length;
            slides.forEach(function (slide, i) {
                slide.classList.toggle('is-active', i === current);
            });
            dots.forEach(function (dot, i) {
                dot.classList.toggle('is-active', i === current);
            });
        }

        function start() {
            if (slides.length < 2 || reduceMotion) return;
            timer = window.setInterval(function () { show(current + 1); }, 8000);
        }

        dots.forEach(function (dot) {
            dot.addEventListener('click', function () {
                window.clearInterval(timer);
                show(parseInt(dot.dataset.slideTo, 10));
                start();
            });
        });

        // На скрытой вкладке крутить слайды незачем
        document.addEventListener('visibilitychange', function () {
            if (document.hidden) { window.clearInterval(timer); } else { start(); }
        });

        start();
    }

    // --------------------------------------- даты: выезд всегда позже заезда
    function syncDates(root) {
        var checkIn = root.querySelector('[data-check-in]');
        var checkOut = root.querySelector('[data-check-out]');
        if (!checkIn || !checkOut) return;

        var today = new Date().toISOString().slice(0, 10);
        checkIn.min = today;
        checkOut.min = checkIn.value || today;

        checkIn.addEventListener('change', function () {
            var next = new Date(checkIn.value);
            next.setDate(next.getDate() + 1);
            var minOut = next.toISOString().slice(0, 10);
            checkOut.min = minOut;
            if (!checkOut.value || checkOut.value <= checkIn.value) {
                checkOut.value = minOut;
            }
        });
    }

    document.querySelectorAll('form').forEach(syncDates);

    // ------------------------------------------- формы, отправляемые по AJAX
    document.querySelectorAll('[data-ajax-form]').forEach(function (form) {
        form.addEventListener('submit', function (event) {
            event.preventDefault();

            var note = form.querySelector('[data-form-note]');
            var button = form.querySelector('button[type="submit"]');
            if (button) button.disabled = true;

            fetch(form.action, {
                method: 'POST',
                body: new FormData(form),
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
                .then(function (response) {
                    return response.json().then(function (data) {
                        return { ok: response.ok, data: data };
                    });
                })
                .then(function (result) {
                    if (note) {
                        note.textContent = result.ok
                            ? (result.data.message || form.dataset.successText || 'Готово! Мы свяжемся с вами.')
                            : (form.dataset.errorText || 'Проверьте правильность заполнения.');
                        note.className = 'form__note ' + (result.ok ? 'is-ok' : 'is-error');
                    }
                    if (result.ok) form.reset();
                })
                .catch(function () {
                    if (note) {
                        note.textContent = 'Ошибка соединения. Попробуйте позже.';
                        note.className = 'form__note is-error';
                    }
                })
                .finally(function () {
                    if (button) button.disabled = false;
                });
        });
    });

    // ----------------------------------------- пересчёт итога при выборе услуг
    // Стоимость доп. услуг зависит от числа ночей и гостей, поэтому считает
    // сервер: форма пересчёта уходит методом GET и перерисовывает страницу.
    // Бронь при этом не создаётся — она создаётся только по POST.
    document.querySelectorAll('[data-autosubmit]').forEach(function (form) {
        form.querySelectorAll('input, select').forEach(function (input) {
            input.addEventListener('change', function () { form.submit(); });
        });
    });
})();
