/**
 * Motor Interactivo del Catálogo SHIBUI
 * Incluye: Vitrina 360°, Bolsa Mayorista/Detal, Cuentas de Usuario Registradas y Reseñas Verificadas
 */

const CART_STORAGE_KEY = 'shibui_django_cart_v1';

let cart = [];
let currentUser = window.CURRENT_USER || {
    is_authenticated: false,
    id: null,
    username: '',
    name: '',
    email: '',
    phone: '',
    city: '',
    preferred_size: 'S'
};

let activeModalProduct = null;
let selectedSize = '';
let selectedColor = null;
let selectedQty = 1;

document.addEventListener('DOMContentLoaded', () => {
    if (window.CURRENT_USER) {
        currentUser = window.CURRENT_USER;
    }
    loadCart();
    syncUserProfileUI();
    renderCart();
});

function loadCart() {
    try {
        const raw = localStorage.getItem(CART_STORAGE_KEY);
        cart = raw ? JSON.parse(raw) : [];
    } catch (e) {
        cart = [];
    }
}

function saveCart() {
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(cart));
    renderCart();
}

/* =========================================================================
   CUENTAS DE USUARIO REGISTRADAS Y SECCIÓN DE RESEÑAS (userSectionModal)
   ========================================================================= */
function syncUserProfileUI() {
    const isAuth = Boolean(currentUser && currentUser.is_authenticated);
    const navLabel = document.getElementById('navUserNameLabel');
    const headerTitle = document.getElementById('userModalHeaderName');
    const headerSub = document.getElementById('userModalHeaderSub');

    if (isAuth) {
        const firstName = (currentUser.name || currentUser.username || 'Usuario').split(' ')[0];
        if (navLabel) navLabel.textContent = `Hola, ${firstName}`;
        if (headerTitle) headerTitle.textContent = `Cuenta de ${currentUser.name || currentUser.username}`;
        if (headerSub) headerSub.textContent = `Sesión iniciada (@${currentUser.username}) · Puedes publicar reseñas`;
    } else {
        if (navLabel) navLabel.textContent = 'Iniciar Sesión / Cuenta';
        if (headerTitle) headerTitle.textContent = 'Sección de Usuario · SHIBUI';
        if (headerSub) headerSub.textContent = 'Inicia sesión con tu cuenta registrada para comentar prendas';
    }

    // Mostrar u ocultar bloqueo de reseñas en Modal de Usuario
    const authReqBox = document.getElementById('uReviewAuthRequiredBox');
    const globalRevForm = document.getElementById('userGlobalReviewForm');
    if (authReqBox) authReqBox.classList.toggle('hidden', isAuth);
    if (globalRevForm) globalRevForm.classList.toggle('hidden', !isAuth);

    // Mostrar u ocultar bloqueo de reseñas en Modal de Prenda
    const modalAuthReq = document.getElementById('modalReviewAuthRequired');
    const modalRevForm = document.getElementById('modalReviewForm');
    if (modalAuthReq) modalAuthReq.classList.toggle('hidden', isAuth);
    if (modalRevForm) modalRevForm.classList.toggle('hidden', !isAuth);

    // Mostrar u ocultar vista de Invitado vs Cuenta Activa en pestaña "Mi Cuenta"
    const guestBox = document.getElementById('uAccountGuestBox');
    const loggedBox = document.getElementById('uAccountLoggedBox');
    if (guestBox) guestBox.classList.toggle('hidden', isAuth);
    if (loggedBox) loggedBox.classList.toggle('hidden', !isAuth);

    if (isAuth) {
        const uRevLoggedName = document.getElementById('uRevLoggedName');
        const modalRevLoggedUser = document.getElementById('modalRevLoggedUser');
        const profLoggedFullName = document.getElementById('profLoggedFullName');
        const profLoggedUsername = document.getElementById('profLoggedUsername');

        if (uRevLoggedName) uRevLoggedName.textContent = `${currentUser.name} (@${currentUser.username})`;
        if (modalRevLoggedUser) modalRevLoggedUser.textContent = currentUser.name;
        if (profLoggedFullName) profLoggedFullName.textContent = currentUser.name;
        if (profLoggedUsername) profLoggedUsername.textContent = `@${currentUser.username}${currentUser.email ? ' · ' + currentUser.email : ''}`;

        const profName = document.getElementById('profName');
        const profPhone = document.getElementById('profPhone');
        const profCity = document.getElementById('profCity');
        const profSize = document.getElementById('profSize');
        const uRevSize = document.getElementById('uRevSize');

        if (profName) profName.value = currentUser.name || '';
        if (profPhone) profPhone.value = currentUser.phone || '';
        if (profCity) profCity.value = currentUser.city || '';
        if (profSize) profSize.value = currentUser.preferred_size || 'S';
        if (uRevSize && currentUser.preferred_size) uRevSize.value = currentUser.preferred_size;
    }
}

function showAuthFeedback(message, isError = true) {
    const el = document.getElementById('uAuthFeedback');
    if (!el) return;
    el.textContent = message;
    el.className = isError
        ? 'p-3 rounded-2xl text-xs font-bold text-center bg-red-50 border border-red-200 text-red-700'
        : 'p-3 rounded-2xl text-xs font-bold text-center bg-emerald-50 border border-emerald-200 text-emerald-800';
    el.classList.remove('hidden');
}

function hideAuthFeedback() {
    const el = document.getElementById('uAuthFeedback');
    if (el) el.classList.add('hidden');
}

function toggleGuestAuthForm(mode = 'login') {
    hideAuthFeedback();
    const loginForm = document.getElementById('uLoginForm');
    const regForm = document.getElementById('uRegisterForm');
    const btnLogin = document.getElementById('btnSwitchAuthLogin');
    const btnReg = document.getElementById('btnSwitchAuthRegister');

    if (loginForm) loginForm.classList.toggle('hidden', mode !== 'login');
    if (regForm) regForm.classList.toggle('hidden', mode !== 'register');

    if (btnLogin) {
        btnLogin.className = mode === 'login'
            ? 'py-2 rounded-full bg-[#2B2B2B] text-white text-xs font-bold transition'
            : 'py-2 rounded-full text-zinc-600 hover:text-black text-xs font-bold transition';
    }
    if (btnReg) {
        btnReg.className = mode === 'register'
            ? 'py-2 rounded-full bg-[#2B2B2B] text-white text-xs font-bold transition'
            : 'py-2 rounded-full text-zinc-600 hover:text-black text-xs font-bold transition';
    }
}

function openAuthSubTab(mode = 'login') {
    switchUserSectionTab('profile');
    toggleGuestAuthForm(mode);
}

function fillDemoCustomerLogin() {
    const uInput = document.getElementById('loginUsername');
    const pInput = document.getElementById('loginPassword');
    if (uInput) uInput.value = 'camila';
    if (pInput) pInput.value = '1234';
}

async function submitUserLogin(e) {
    e.preventDefault();
    hideAuthFeedback();

    const username = (document.getElementById('loginUsername').value || '').trim();
    const password = (document.getElementById('loginPassword').value || '').trim();
    if (!username || !password) return;

    const btn = document.getElementById('btnSubmitLogin');
    btn.disabled = true;
    btn.textContent = 'Verificando cuenta...';

    try {
        const res = await fetch('/api/auth/login/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();
        if (data.status === 'success') {
            currentUser = data.user;
            window.CURRENT_USER = data.user;
            syncUserProfileUI();
            switchUserSectionTab('write-review');
        } else {
            showAuthFeedback(data.message || 'Credenciales incorrectas', true);
        }
    } catch (err) {
        showAuthFeedback('Error de conexión al iniciar sesión', true);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Iniciar Sesión';
    }
}

async function submitUserRegister(e) {
    e.preventDefault();
    hideAuthFeedback();

    const payload = {
        name: (document.getElementById('regName').value || '').trim(),
        username: (document.getElementById('regUsername').value || '').trim(),
        email: (document.getElementById('regEmail').value || '').trim(),
        password: (document.getElementById('regPassword').value || '').trim(),
        phone: (document.getElementById('regPhone').value || '').trim(),
        city: (document.getElementById('regCity').value || '').trim(),
        preferred_size: document.getElementById('regSize').value || 'S'
    };

    const btn = document.getElementById('btnSubmitRegister');
    btn.disabled = true;
    btn.textContent = 'Creando tu cuenta...';

    try {
        const res = await fetch('/api/auth/register/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.status === 'success') {
            currentUser = data.user;
            window.CURRENT_USER = data.user;
            syncUserProfileUI();
            switchUserSectionTab('write-review');
        } else {
            showAuthFeedback(data.message || 'No se pudo registrar la cuenta', true);
        }
    } catch (err) {
        showAuthFeedback('Error de conexión al crear la cuenta', true);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Crear Mi Cuenta y Comentar';
    }
}

async function logoutCustomerUser() {
    try {
        const res = await fetch('/api/auth/logout/', { method: 'POST' });
        const data = await res.json();
        if (data.status === 'success') {
            currentUser = data.user;
            window.CURRENT_USER = data.user;
            syncUserProfileUI();
            toggleGuestAuthForm('login');
        }
    } catch (err) {
        alert('Error al cerrar sesión');
    }
}

async function saveUserProfile(e) {
    e.preventDefault();
    if (!currentUser || !currentUser.is_authenticated) return;

    const btn = document.getElementById('btnSaveProfile');
    btn.disabled = true;
    btn.textContent = 'Guardando...';

    try {
        const res = await fetch('/api/auth/profile/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: (document.getElementById('profName').value || '').trim(),
                phone: (document.getElementById('profPhone').value || '').trim(),
                city: (document.getElementById('profCity').value || '').trim(),
                preferred_size: document.getElementById('profSize').value || 'S'
            })
        });
        const data = await res.json();
        if (data.status === 'success') {
            currentUser = data.user;
            window.CURRENT_USER = data.user;
            syncUserProfileUI();
            switchUserSectionTab('write-review');
        }
    } catch (err) {
        alert('Error al actualizar tu cuenta');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Guardar Cambios en Mi Cuenta';
    }
}

function openUserSectionModal(initialTab = 'write-review') {
    const products = window.CATALOG_PRODUCTS || [];
    const select = document.getElementById('uRevProductSelect');
    if (select) {
        select.innerHTML = products.map(p =>
            `<option value="${p.id}">${p.name} (${p.category})</option>`
        ).join('');
    }

    syncUserProfileUI();
    renderUserSectionAllReviews();
    switchUserSectionTab(initialTab);

    const modal = document.getElementById('userSectionModal');
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }
}

function closeUserSectionModal() {
    const modal = document.getElementById('userSectionModal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}

function switchUserSectionTab(tab) {
    ['write-review', 'all-reviews', 'profile'].forEach(t => {
        const panel = document.getElementById('uTabPanel-' + t);
        const btn = document.getElementById('uTabBtn-' + t);
        if (panel) panel.classList.toggle('hidden', t !== tab);
        if (btn) {
            btn.className = (t === tab)
                ? 'py-3 border-b-2 border-[#141414] text-[#141414]'
                : 'py-3 border-b-2 border-transparent text-zinc-400 hover:text-black';
        }
    });
}

function setGlobalReviewStars(rating) {
    document.getElementById('uRevRating').value = rating;
    const buttons = document.querySelectorAll('#uRevStarsPicker button');
    buttons.forEach((btn, idx) => {
        btn.className = (idx < rating)
            ? 'text-2xl text-amber-400 hover:scale-110 transition'
            : 'text-2xl text-zinc-300 hover:scale-110 transition';
    });
    const labels = ['1/5 Regular', '2/5 Aceptable', '3/5 Bueno', '4/5 Muy Bueno', '5/5 Excelente'];
    const txt = document.getElementById('uRevStarsText');
    if (txt) txt.textContent = labels[rating - 1] || '5/5 Excelente';
}

function renderUserSectionAllReviews() {
    const products = window.CATALOG_PRODUCTS || [];
    const allReviews = [];
    products.forEach(p => {
        (p.reviews || []).forEach(r => {
            allReviews.push({
                ...r,
                product_id: p.id,
                product_name: p.name,
                product_img: p.image_url
            });
        });
    });

    const countEl = document.getElementById('uTotalReviewsCount');
    if (countEl) countEl.textContent = allReviews.length;

    const container = document.getElementById('uAllReviewsContainer');
    if (!container) return;

    if (allReviews.length === 0) {
        container.innerHTML = `<p class="text-center py-8 text-xs text-zinc-400">Aún no hay reseñas publicadas. ¡Sé la primera persona en opinar!</p>`;
        return;
    }

    container.innerHTML = allReviews.map(rev => `
        <div class="p-3.5 rounded-2xl bg-[#F6F6F6] border border-zinc-200/70 flex items-start gap-3">
            <img src="${rev.product_img}" alt="${rev.product_name}"
                 onclick="closeUserSectionModal(); openProductDetailModal(${rev.product_id}, 'reviews')"
                 class="w-14 h-16 object-cover rounded-xl cursor-pointer shrink-0">
            <div class="flex-1 min-w-0">
                <div class="flex items-center justify-between gap-2">
                    <span class="text-xs font-extrabold text-[#141414] flex items-center gap-1">
                        ${rev.author_name}
                        <i class="fa-solid fa-circle-check text-[10px] text-emerald-600" title="Cuenta registrada"></i>
                    </span>
                    <span class="text-amber-400 text-xs">${'★'.repeat(rev.rating)}${'☆'.repeat(5 - rev.rating)}</span>
                </div>
                <p class="text-[11px] font-semibold text-zinc-500 mt-0.5">
                    ${rev.product_name} · Talla ${rev.size_purchased} (${rev.fit_feedback})
                </p>
                <p class="text-xs text-zinc-700 mt-1 leading-relaxed">"${rev.comment}"</p>
            </div>
        </div>
    `).join('');
}

async function submitGlobalReview(e) {
    e.preventDefault();
    if (!currentUser || !currentUser.is_authenticated) {
        openAuthSubTab('login');
        return;
    }

    const productId = parseInt(document.getElementById('uRevProductSelect').value);
    const sizePurchased = document.getElementById('uRevSize').value;
    const fitFeedback = document.getElementById('uRevFit').value;
    const rating = parseInt(document.getElementById('uRevRating').value || '5');
    const comment = document.getElementById('uRevComment').value.trim();

    if (!comment) return;

    const btn = document.getElementById('btnSubmitGlobalReview');
    btn.disabled = true;
    btn.textContent = 'Publicando reseña...';

    try {
        const res = await fetch('/api/reviews/add/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                product_id: productId,
                rating,
                size_purchased: sizePurchased,
                fit_feedback: fitFeedback,
                comment
            })
        });
        const data = await res.json();
        if (data.status === 'success') {
            const products = window.CATALOG_PRODUCTS || [];
            const prod = products.find(p => p.id === productId);
            if (prod) {
                prod.reviews = [data.review, ...(prod.reviews || [])];
                prod.avg_rating = data.avg_rating;
                prod.reviews_count = data.reviews_count;
            }
            document.getElementById('uRevComment').value = '';
            renderUserSectionAllReviews();
            switchUserSectionTab('all-reviews');
        } else if (data.require_auth) {
            currentUser.is_authenticated = false;
            syncUserProfileUI();
            openAuthSubTab('login');
        } else {
            alert(data.message || 'No se pudo guardar la reseña');
        }
    } catch (err) {
        alert('Error al publicar la reseña');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Publicar Reseña';
    }
}

/* =========================================================================
   MODAL DE PRENDA (Vitrina 360° + Miniaturas + Pestaña de Reseñas)
   ========================================================================= */
function openProductDetailModal(productId, initialTab = 'about') {
    const products = window.CATALOG_PRODUCTS || [];
    const product = products.find(p => p.id === productId);
    if (!product) return;

    activeModalProduct = product;
    selectedSize = (product.sizes && product.sizes.length > 0) ? product.sizes[0] : 'Única';
    selectedColor = (product.colors && product.colors.length > 0) ? product.colors[0] : { name: 'Negro', hex: '#141414' };
    selectedQty = 1;

    const cfg = window.STORE_CONFIG || { currencySymbol: '$', bcvRate: 45.80, globalMinUnits: 6 };
    const sym = cfg.currencySymbol || '$';

    document.getElementById('modalProductSku').textContent = `REF · ${product.sku || 'SHB'}`;
    document.getElementById('modalProductImg').src = product.image_url;
    document.getElementById('modalProductImg').alt = product.name;
    document.getElementById('modalProductCategory').textContent = product.category;
    document.getElementById('modalProductName').textContent = product.name;
    document.getElementById('modalProductDesc').textContent = product.description || '';

    const immBadge = document.getElementById('modalImmediateBadge');
    if (immBadge) {
        immBadge.classList.toggle('hidden', !product.is_immediate);
    }

    const retailBs = (product.price_retail * cfg.bcvRate).toFixed(2);
    document.getElementById('modalPriceRetailUsd').textContent = `${sym}${product.price_retail.toFixed(2)} USD`;
    document.getElementById('modalPriceRetailBs').textContent = `Bs. ${retailBs}`;
    document.getElementById('modalPriceWholesaleUsd').textContent = `${sym}${product.price_wholesale.toFixed(2)} USD`;
    document.getElementById('modalDiscountBadge').textContent = `-${product.discount_percent}%`;
    document.getElementById('modalWholesaleRule').textContent = `Desde ${product.wholesale_min_qty} uds o ${cfg.globalMinUnits} surtidas`;

    const btnWhQty = document.getElementById('btnSetWholesaleQty');
    if (btnWhQty) {
        btnWhQty.innerHTML = `⚡ Llevar mínimo al mayor (${product.wholesale_min_qty} uds)`;
    }

    renderModalThumbs();
    renderModalColors();
    renderModalSizes();
    renderModalReviews();
    syncUserProfileUI();
    updateModalQtyUI();
    switchModalTab(initialTab);

    const modal = document.getElementById('productDetailModal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

function closeProductDetailModal() {
    const modal = document.getElementById('productDetailModal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}

function cycleNextProductInModal() {
    const products = window.CATALOG_PRODUCTS || [];
    if (!products.length || !activeModalProduct) return;
    const currentIndex = products.findIndex(p => p.id === activeModalProduct.id);
    const nextIndex = (currentIndex + 1) % products.length;
    openProductDetailModal(products[nextIndex].id);
}

function setModalMainImage(url, index) {
    const mainImg = document.getElementById('modalProductImg');
    if (!mainImg) return;
    mainImg.src = url;
    document.querySelectorAll('.modal-thumb-btn').forEach((btn, i) => {
        if (i === index) {
            btn.className = 'modal-thumb-btn shrink-0 w-20 sm:w-24 rounded-2xl p-1.5 transition border bg-[#333333] border-[#333333] shadow-md scale-105';
        } else {
            btn.className = 'modal-thumb-btn shrink-0 w-20 sm:w-24 rounded-2xl p-1.5 transition border bg-[#F3F3F3] border-zinc-200/80 hover:border-zinc-400';
        }
    });
}

function renderModalThumbs() {
    const container = document.getElementById('modalThumbsRow');
    if (!container || !activeModalProduct) return;

    const productImages = (activeModalProduct.images && activeModalProduct.images.length > 0)
        ? activeModalProduct.images
        : (activeModalProduct.image_url ? [activeModalProduct.image_url] : []);

    if (productImages.length > 1) {
        // Mostrar hasta 4 fotografías de esta prenda para alternar vistas con scroll lateral
        container.innerHTML = productImages.slice(0, 4).map((imgUrl, idx) => {
            const isCurrent = idx === 0;
            return `
                <button type="button" onclick="setModalMainImage('${imgUrl}', ${idx})"
                        title="Ver foto ${idx + 1}"
                        class="modal-thumb-btn shrink-0 w-20 sm:w-24 rounded-2xl p-1.5 transition border ${isCurrent ? 'bg-[#333333] border-[#333333] shadow-md scale-105' : 'bg-[#F3F3F3] border-zinc-200/80 hover:border-zinc-400'}">
                    <img src="${imgUrl}" alt="Foto ${idx+1}" class="w-full h-16 object-cover rounded-xl">
                </button>
            `;
        }).join('');
    } else {
        const products = window.CATALOG_PRODUCTS || [];
        const currentIndex = products.findIndex(p => p.id === activeModalProduct.id);
        const thumbs = [];

        for (let i = 0; i < Math.min(4, products.length); i++) {
            thumbs.push(products[(currentIndex + i) % products.length]);
        }

        container.innerHTML = thumbs.map((item) => {
            const isCurrent = item.id === activeModalProduct.id;
            return `
                <button type="button" onclick="openProductDetailModal(${item.id})"
                        class="modal-thumb-btn shrink-0 w-20 sm:w-24 rounded-2xl p-1.5 transition border ${isCurrent ? 'bg-[#333333] border-[#333333] shadow-md scale-105' : 'bg-[#F3F3F3] border-zinc-200/80 hover:border-zinc-400'}">
                    <img src="${item.image_url}" alt="${item.name}" class="w-full h-16 object-cover rounded-xl">
                </button>
            `;
        }).join('');
    }
}

function renderModalReviews() {
    if (!activeModalProduct) return;
    const reviews = activeModalProduct.reviews || [];
    const avgBadge = document.getElementById('modalAvgRatingBadge');
    const tabCount = document.getElementById('modalReviewsCountTab');
    const listEl = document.getElementById('modalReviewsList');

    if (avgBadge) avgBadge.textContent = (activeModalProduct.avg_rating || 5.0).toFixed(1);
    if (tabCount) tabCount.textContent = reviews.length;
    if (!listEl) return;

    if (reviews.length === 0) {
        listEl.innerHTML = `
            <div class="p-3 rounded-2xl bg-[#FAFAFA] border border-zinc-100 text-center text-xs text-zinc-400">
                Sé la primera persona en dejar una reseña sobre <strong>${activeModalProduct.name}</strong>.
            </div>
        `;
    } else {
        listEl.innerHTML = reviews.map(r => `
            <div class="p-3 rounded-2xl bg-[#FAFAFA] border border-zinc-200/60">
                <div class="flex items-center justify-between">
                    <span class="text-xs font-extrabold text-[#141414] flex items-center gap-1">
                        ${r.author_name}
                        <i class="fa-solid fa-circle-check text-[10px] text-emerald-600" title="Cuenta registrada"></i>
                    </span>
                    <span class="text-amber-400 text-xs">${'★'.repeat(r.rating)}${'☆'.repeat(5 - r.rating)}</span>
                </div>
                <p class="text-[10px] font-semibold text-zinc-400 mt-0.5">
                    Talla comprada: <strong class="text-zinc-700">${r.size_purchased}</strong> · ${r.fit_feedback} · ${r.date}
                </p>
                <p class="text-xs text-zinc-700 mt-1 leading-snug">"${r.comment}"</p>
            </div>
        `).join('');
    }
}

function setModalReviewStars(rating) {
    document.getElementById('modalRevRating').value = rating;
    const buttons = document.querySelectorAll('#modalStarsPicker button');
    buttons.forEach((btn, idx) => {
        btn.className = (idx < rating)
            ? 'text-base text-amber-400 hover:scale-110 transition'
            : 'text-base text-zinc-300 hover:scale-110 transition';
    });
}

async function submitModalProductReview(e) {
    e.preventDefault();
    if (!activeModalProduct) return;
    if (!currentUser || !currentUser.is_authenticated) {
        window.location.href = '/login/';
        return;
    }

    const fitEl = document.getElementById('modalRevFit');
    const fitFeedback = fitEl ? fitEl.value : 'Fiel a la talla';
    const rating = parseInt(document.getElementById('modalRevRating').value || '5');
    const comment = document.getElementById('modalRevComment').value.trim();

    if (!comment) return;

    const btn = document.getElementById('btnSubmitModalRev');
    btn.disabled = true;
    btn.textContent = 'Publicando...';

    try {
        const res = await fetch('/api/reviews/add/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                product_id: activeModalProduct.id,
                rating,
                size_purchased: selectedSize || 'M',
                fit_feedback: fitFeedback,
                comment
            })
        });
        const data = await res.json();
        if (data.status === 'success') {
            activeModalProduct.reviews = [data.review, ...(activeModalProduct.reviews || [])];
            activeModalProduct.avg_rating = data.avg_rating;
            activeModalProduct.reviews_count = data.reviews_count;
            document.getElementById('modalRevComment').value = '';
            renderModalReviews();
        } else if (data.require_auth) {
            currentUser.is_authenticated = false;
            syncUserProfileUI();
        } else {
            alert(data.message || 'No se pudo publicar la reseña');
        }
    } catch (err) {
        alert('Error al enviar reseña');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Publicar Comentario';
    }
}

function renderModalColors() {
    if (!activeModalProduct) return;
    const container = document.getElementById('modalColorsContainer');
    const label = document.getElementById('modalSelectedColorName');
    if (!container) return;

    label.textContent = selectedColor ? selectedColor.name : 'Único';
    container.innerHTML = '';

    (activeModalProduct.colors || []).forEach(c => {
        const btn = document.createElement('button');
        btn.type = 'button';
        const isSel = selectedColor && selectedColor.name === c.name;
        btn.className = `st-color-dot ${isSel ? 'selected' : ''}`;
        btn.style.backgroundColor = c.hex;
        btn.title = c.name;
        btn.onclick = () => {
            selectedColor = c;
            renderModalColors();
            updateModalWhatsappLink();
        };
        container.appendChild(btn);
    });
}

function renderModalSizes() {
    if (!activeModalProduct) return;
    const container = document.getElementById('modalSizesContainer');
    const label = document.getElementById('modalSelectedSizeName');
    if (!container) return;

    label.textContent = selectedSize || 'Única';
    container.innerHTML = '';

    (activeModalProduct.sizes || ['Única']).forEach(sizeName => {
        const btn = document.createElement('button');
        btn.type = 'button';
        const isSel = selectedSize === sizeName;
        btn.className = `st-size-text-btn ${isSel ? 'selected' : ''}`;
        btn.textContent = sizeName;
        btn.onclick = () => {
            selectedSize = sizeName;
            renderModalSizes();
            updateModalWhatsappLink();
        };
        container.appendChild(btn);
    });
}

function switchModalTab(tab) {
    ['closet', 'about', 'reviews'].forEach(t => {
        const panel = document.getElementById('mTabPanel-' + t);
        const btn = document.getElementById('mTabBtn-' + t);
        if (panel) panel.classList.toggle('hidden', t !== tab);
        if (btn) {
            btn.className = (t === tab)
                ? 'py-2.5 border-b-2 border-[#141414] text-[#141414]'
                : 'py-2.5 border-b-2 border-transparent text-zinc-400 hover:text-black';
        }
    });
}

function adjustModalQty(delta) {
    if (!activeModalProduct) return;
    selectedQty = Math.max(1, selectedQty + delta);
    updateModalQtyUI();
}

function setModalWholesaleQty() {
    if (!activeModalProduct) return;
    selectedQty = activeModalProduct.wholesale_min_qty || 4;
    updateModalQtyUI();
}

function updateModalQtyUI() {
    if (!activeModalProduct) return;
    const cfg = window.STORE_CONFIG || { currencySymbol: '$', globalMinUnits: 6, combineWholesale: true };
    const sym = cfg.currencySymbol || '$';

    document.getElementById('modalQtyValue').textContent = selectedQty;

    const currentCartUnits = cart.reduce((acc, i) => acc + i.quantity, 0);
    const totalWithSelection = currentCartUnits + selectedQty;
    const qualifiesWholesale = (selectedQty >= activeModalProduct.wholesale_min_qty) ||
                               (cfg.combineWholesale && totalWithSelection >= cfg.globalMinUnits);

    const statusEl = document.getElementById('modalLivePriceStatus');
    if (statusEl) {
        if (qualifiesWholesale) {
            statusEl.innerHTML = `<span class="text-emerald-700 font-bold">🔥 ¡Aplica Precio al Mayor (${sym}${activeModalProduct.price_wholesale.toFixed(2)} c/u)!</span>`;
        } else {
            const neededModel = activeModalProduct.wholesale_min_qty - selectedQty;
            statusEl.innerHTML = `Tarifa Detal (${sym}${activeModalProduct.price_retail.toFixed(2)} c/u) · Faltan ${neededModel} uds para Mayor`;
        }
    }
    updateModalWhatsappLink();
}

function updateModalWhatsappLink() {
    if (!activeModalProduct) return;
    const cfg = window.STORE_CONFIG || {};
    const phone = (cfg.ownerPhone || '').replace(/\D/g, '');
    const msg = `Hola ${cfg.storeName || 'SHIBUI'}, me interesa la prenda *${activeModalProduct.name}* (Ref: ${activeModalProduct.sku}) en Talla *${selectedSize}* y Color *${selectedColor ? selectedColor.name : 'Estándar'}* (${selectedQty} unidad/es).`;
    const btn = document.getElementById('modalWhatsappDirectBtn');
    if (btn) {
        btn.href = `https://wa.me/${phone}?text=${encodeURIComponent(msg)}`;
    }
}

function addFromModalToCart(buyNow = false) {
    if (!activeModalProduct) return;
    addToCart({
        productId: activeModalProduct.id,
        name: activeModalProduct.name,
        sku: activeModalProduct.sku,
        image_url: activeModalProduct.image_url,
        price_retail: activeModalProduct.price_retail,
        price_wholesale: activeModalProduct.price_wholesale,
        wholesale_min_qty: activeModalProduct.wholesale_min_qty,
        size: selectedSize || 'Única',
        color: selectedColor || { name: 'Negro', hex: '#141414' },
        quantity: selectedQty
    });
    closeProductDetailModal();
    if (buyNow) {
        openCheckoutModal();
    } else {
        toggleCartDrawer(true);
    }
}

/* =========================================================================
   GESTIÓN DEL CARRITO LATERAL Y BARRA INFERIOR
   ========================================================================= */
function addToCart(newItem) {
    const key = `${newItem.productId}_${newItem.size}_${newItem.color.name}`;
    const existing = cart.find(i => i.key === key);
    if (existing) {
        existing.quantity += newItem.quantity;
    } else {
        cart.push({ ...newItem, key });
    }
    saveCart();
}

function updateCartItemQty(key, delta) {
    const idx = cart.findIndex(i => i.key === key);
    if (idx === -1) return;
    cart[idx].quantity += delta;
    if (cart[idx].quantity <= 0) {
        cart.splice(idx, 1);
    }
    saveCart();
}

function removeCartItem(key) {
    cart = cart.filter(i => i.key !== key);
    saveCart();
}

function clearCart() {
    cart = [];
    saveCart();
}

function toggleCartDrawer(open) {
    const drawer = document.getElementById('cartDrawer');
    const backdrop = document.getElementById('cartDrawerBackdrop');
    if (!drawer || !backdrop) return;

    if (open) {
        backdrop.classList.remove('hidden');
        drawer.classList.remove('translate-x-full');
    } else {
        backdrop.classList.add('hidden');
        drawer.classList.add('translate-x-full');
    }
}

function calculateCartTotals() {
    const cfg = window.STORE_CONFIG || { currencySymbol: '$', bcvRate: 45.80, combineWholesale: true, globalMinUnits: 6 };
    const totalUnits = cart.reduce((sum, item) => sum + item.quantity, 0);
    const isGlobalWholesale = cfg.combineWholesale && totalUnits >= cfg.globalMinUnits;

    const modelUnits = {};
    cart.forEach(item => {
        modelUnits[item.productId] = (modelUnits[item.productId] || 0) + item.quantity;
    });

    let subtotalRetail = 0;
    let totalFinal = 0;

    const enrichedItems = cart.map(item => {
        const modelTotal = modelUnits[item.productId] || item.quantity;
        const qualifiesWholesale = isGlobalWholesale || (modelTotal >= item.wholesale_min_qty);
        const unitPrice = qualifiesWholesale ? item.price_wholesale : item.price_retail;
        const lineRetail = item.price_retail * item.quantity;
        const lineFinal = unitPrice * item.quantity;

        subtotalRetail += lineRetail;
        totalFinal += lineFinal;

        return {
            ...item,
            qualifiesWholesale,
            unitPrice,
            lineFinal,
            lineBs: lineFinal * cfg.bcvRate
        };
    });

    const wholesaleSavings = Math.max(0, subtotalRetail - totalFinal);
    const totalBs = totalFinal * cfg.bcvRate;

    return {
        items: enrichedItems,
        totalUnits,
        isGlobalWholesale,
        subtotalRetail,
        wholesaleSavings,
        totalFinal,
        totalBs
    };
}

function renderCart() {
    const cfg = window.STORE_CONFIG || { currencySymbol: '$', bcvRate: 45.80, globalMinUnits: 6 };
    const sym = cfg.currencySymbol || '$';
    const summary = calculateCartTotals();

    const badge = document.getElementById('navCartBadge');
    if (badge) badge.textContent = summary.totalUnits;

    const dockBadge = document.getElementById('dockCartBadge');
    if (dockBadge) dockBadge.textContent = summary.totalUnits;

    const progressBar = document.getElementById('wholesaleProgressBar');
    const statusText = document.getElementById('wholesaleStatusText');
    const countBadge = document.getElementById('wholesaleCountBadge');

    if (progressBar && statusText && countBadge) {
        const pct = Math.min(100, Math.round((summary.totalUnits / cfg.globalMinUnits) * 100));
        progressBar.style.width = `${pct}%`;
        countBadge.textContent = `${summary.totalUnits} / ${cfg.globalMinUnits}`;

        if (summary.totalUnits >= cfg.globalMinUnits || summary.wholesaleSavings > 0) {
            statusText.innerHTML = `🔥 ¡Precios <strong>AL MAYOR</strong> activados en tu bolsa!`;
        } else {
            const missing = cfg.globalMinUnits - summary.totalUnits;
            statusText.innerHTML = `Agrega <strong>${missing} prenda(s)</strong> más para Mayor Surtido`;
        }
    }

    const container = document.getElementById('cartItemsContainer');
    const footer = document.getElementById('cartFooter');
    if (!container) return;

    if (summary.items.length === 0) {
        container.innerHTML = `
            <div class="py-16 text-center">
                <p class="text-sm text-zinc-500 font-bold">Tu bolsa está vacía</p>
                <p class="text-xs text-zinc-400 mt-1">Selecciona cualquier prenda del catálogo para elegir talla y color.</p>
            </div>
        `;
        if (footer) footer.classList.add('opacity-50', 'pointer-events-none');
    } else {
        if (footer) footer.classList.remove('opacity-50', 'pointer-events-none');
        container.innerHTML = summary.items.map(item => `
            <div class="py-3.5 flex gap-3.5 items-start">
                <img src="${item.image_url}" alt="${item.name}" class="w-20 h-24 object-cover rounded-2xl border border-zinc-100 shrink-0">
                <div class="flex-1 min-w-0">
                    <h4 class="text-sm font-extrabold text-[#141414] truncate">${item.name}</h4>
                    <div class="text-xs text-zinc-500 mt-0.5 space-y-0.5">
                        <p>Talla: <strong class="text-[#141414]">${item.size}</strong></p>
                        <p class="flex items-center gap-1.5">
                            <span>Color:</span>
                            <span class="w-3.5 h-3.5 rounded-full border border-black/20 inline-block" style="background-color: ${item.color.hex};"></span>
                            <span class="text-zinc-600">${item.color.name}</span>
                        </p>
                    </div>

                    <div class="mt-1.5 flex items-baseline gap-2">
                        <span class="text-[11px] font-semibold text-zinc-400">Bs. ${item.lineBs.toFixed(2)}</span>
                        <span class="text-xs font-extrabold text-[#141414]">${sym}${item.lineFinal.toFixed(2)} USD</span>
                        ${item.qualifiesWholesale
                            ? `<span class="text-[9px] font-bold bg-[#2B2B2B] text-white px-2 py-0.5 rounded-full">MAYOR</span>`
                            : `<span class="text-[9px] font-semibold bg-zinc-100 text-zinc-600 px-2 py-0.5 rounded-full">DETAL</span>`
                        }
                    </div>

                    <div class="mt-2 flex items-center justify-between">
                        <div class="inline-flex items-center bg-[#F3F3F3] rounded-full p-0.5">
                            <button type="button" onclick="updateCartItemQty('${item.key}', -1)"
                                    class="w-6 h-6 rounded-full bg-white text-xs font-bold text-[#141414] shadow-2xs">&minus;</button>
                            <span class="px-2.5 text-xs font-extrabold text-[#141414]">${item.quantity}</span>
                            <button type="button" onclick="updateCartItemQty('${item.key}', 1)"
                                    class="w-6 h-6 rounded-full bg-white text-xs font-bold text-[#141414] shadow-2xs">&#43;</button>
                        </div>
                        <button type="button" onclick="removeCartItem('${item.key}')"
                                class="text-xs font-bold text-zinc-400 hover:text-black underline">
                            Quitar
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    const savingsRow = document.getElementById('cartSavingsRow');
    const savingsAmt = document.getElementById('cartSavingsAmount');
    if (savingsRow && savingsAmt) {
        if (summary.wholesaleSavings > 0) {
            savingsRow.classList.remove('hidden');
            savingsRow.classList.add('flex');
            savingsAmt.textContent = `-${sym}${summary.wholesaleSavings.toFixed(2)} USD`;
        } else {
            savingsRow.classList.add('hidden');
            savingsRow.classList.remove('flex');
        }
    }

    const elBs = document.getElementById('cartTotalBs');
    const elUsd = document.getElementById('cartTotalUsd');
    const elUnits = document.getElementById('cartTotalUnits');
    if (elBs) elBs.textContent = `Bs. ${summary.totalBs.toFixed(2)}`;
    if (elUsd) elUsd.textContent = `${sym}${summary.totalFinal.toFixed(2)} USD`;
    if (elUnits) elUnits.textContent = `${summary.totalUnits} pieza(s)`;
}

/* =========================================================================
   PEDIDO Y CONFIRMACIÓN DE ORDEN
   ========================================================================= */
function openCheckoutModal() {
    const summary = calculateCartTotals();
    if (summary.items.length === 0) return;

    const cfg = window.STORE_CONFIG || { currencySymbol: '$' };
    const sym = cfg.currencySymbol || '$';

    toggleCartDrawer(false);

    document.getElementById('checkoutStepForm').classList.remove('hidden');
    document.getElementById('checkoutStepSuccess').classList.add('hidden');

    document.getElementById('chkUnits').textContent = summary.totalUnits;
    document.getElementById('chkTotalUsd').textContent = `${sym}${summary.totalFinal.toFixed(2)} USD`;
    document.getElementById('chkTotalBs').textContent = `Bs. ${summary.totalBs.toFixed(2)}`;
    document.getElementById('chkModeBadge').textContent = summary.wholesaleSavings > 0
        ? `🔥 Tarifa AL MAYOR aplicada (Ahorras ${sym}${summary.wholesaleSavings.toFixed(2)})`
        : `Tarifa AL DETAL`;

    // Pre-llenar datos si el usuario tiene sesión iniciada
    if (currentUser && currentUser.is_authenticated) {
        if (currentUser.name && !document.getElementById('chkName').value) {
            document.getElementById('chkName').value = currentUser.name;
        }
        if (currentUser.phone && !document.getElementById('chkPhone').value) {
            document.getElementById('chkPhone').value = currentUser.phone;
        }
        if (currentUser.city && !document.getElementById('chkCity').value) {
            document.getElementById('chkCity').value = currentUser.city;
        }
    }

    const modal = document.getElementById('checkoutModal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

function closeCheckoutModal() {
    const modal = document.getElementById('checkoutModal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}

async function submitOrder(e) {
    e.preventDefault();
    const summary = calculateCartTotals();
    if (summary.items.length === 0) return;

    const deliveryRadio = document.querySelector('input[name="deliveryType"]:checked');
    const deliveryType = deliveryRadio ? deliveryRadio.value : 'Envío Nacional (MRW / Zoom)';

    const btn = document.getElementById('btnSubmitOrder');
    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin mr-2"></i> PROCESANDO...`;

    const payload = {
        customerName: document.getElementById('chkName').value.trim(),
        customerDni: document.getElementById('chkDni').value.trim(),
        customerPhone: document.getElementById('chkPhone').value.trim(),
        deliveryType: deliveryType,
        customerCity: document.getElementById('chkCity').value.trim(),
        customerAddress: document.getElementById('chkAddress').value.trim(),
        paymentMethod: document.getElementById('chkPayment').value,
        notes: document.getElementById('chkNotes').value.trim(),
        items: summary.items.map(i => ({
            productId: i.productId,
            size: i.size,
            color: i.color,
            quantity: i.quantity
        }))
    };

    try {
        const res = await fetch('/api/orders/create/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (data.status === 'success') {
            document.getElementById('checkoutStepForm').classList.add('hidden');
            document.getElementById('checkoutStepSuccess').classList.remove('hidden');
            document.getElementById('successOrderNumber').textContent = `#${data.order_number}`;
            document.getElementById('successWhatsappBtn').href = data.whatsapp_url;
            clearCart();
        } else {
            alert(data.message || 'No se pudo procesar el pedido');
        }
    } catch (err) {
        alert('Error de conexión al enviar el pedido.');
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<span>CONFIRMAR ORDEN</span> <i class="fa-solid fa-check"></i>`;
    }
}
