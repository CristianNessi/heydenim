let selectedProduct = null;
let selectedSize = null;
let selectedColor = null;
let selectedSizeMaxQty = 0;
let cart = [];
let shippingPrice = 0;
let products = [];
let toastTimer = null;
let gridListenersBound = false;

const $ = (id) => document.getElementById(id);

const SOCIAL_ICONS = {
    instagram: 'fab fa-instagram',
    tiktok:    'fab fa-tiktok',
    facebook:  'fab fa-facebook',
    pinterest: 'fab fa-pinterest',
    youtube:   'fab fa-youtube',
    twitter:   'fab fa-x-twitter',
};

function _buildTopbarSocial(social) {
    if (!social || !Object.keys(social).length) return '';
    return Object.entries(social)
        .filter(([, url]) => url)
        .map(([net, url]) => {
            const icon = SOCIAL_ICONS[net] || 'fas fa-link';
            return `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer" aria-label="${net}" class="topbar__social"><i class="${icon}"></i></a>`;
        }).join('');
}

function _buildFooterSocial(social) {
    if (!social || !Object.keys(social).length) return '';
    return Object.entries(social)
        .filter(([, url]) => url)
        .map(([net, url]) => {
            const icon = SOCIAL_ICONS[net] || 'fas fa-link';
            const label = net.charAt(0).toUpperCase() + net.slice(1);
            return `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer" aria-label="Heydemin en ${label}"><i class="${icon}" aria-hidden="true"></i></a>`;
        }).join('');
}

function escapeHtml(text) {
    const el = document.createElement('span');
    el.textContent = text ?? '';
    return el.innerHTML;
}

function formatPrice(value) {
    return `€${Number(value).toFixed(2)}`;
}

function productImages(p) {
    if (p.images) {
        return p.images.split(',').map(s => s.trim()).filter(Boolean);
    }
    return p.image ? [p.image] : ['/static/images/no-image.jpg'];
}

function productImage(p) {
    return productImages(p)[0] || '/static/images/no-image.jpg';
}

function itemDiscount(item) {
    const liveProduct = products.find((p) => p.id === item.id);
    return Math.max(0, Math.min(100, Number(liveProduct?.discount ?? item.discount ?? 0) || 0));
}

function itemFinalUnitPrice(item) {
    const discount = itemDiscount(item);
    return Number(item.price) * (1 - discount / 100);
}

function buildProductThumbs(imgs, productId) {
    if (imgs.length <= 1) return '';
    return [
        '<div class="product-thumbs" aria-label="Imagenes del producto">',
        ...imgs.map((src, index) => [
            `<button type="button" class="product-thumb${index === 0 ? ' active' : ''}" data-action="thumb" data-id="${productId}" data-src="${escapeHtml(src)}" aria-label="Ver imagen ${index + 1}">`,
            `<img src="${escapeHtml(src)}" alt="" loading="lazy">`,
            '</button>',
        ].join('')),
        '</div>',
    ].join('');
}

function selectProductThumb(btn) {
    const card = btn.closest('.product');
    if (!card) return;
    const main = card.querySelector('[data-gallery-main]');
    if (!main) return;

    main.src = btn.dataset.src;
    card.querySelectorAll('.product-thumb').forEach((thumb) => thumb.classList.remove('active'));
    btn.classList.add('active');
}

function selectProductImage(card, index) {
    const thumbs = [...card.querySelectorAll('.product-thumb')];
    if (!thumbs.length) return;
    const nextIndex = (index + thumbs.length) % thumbs.length;
    selectProductThumb(thumbs[nextIndex]);
}

function stepProductImage(btn, delta) {
    const card = btn.closest('.product');
    if (!card) return;
    const thumbs = [...card.querySelectorAll('.product-thumb')];
    const currentIndex = Math.max(0, thumbs.findIndex((thumb) => thumb.classList.contains('active')));
    selectProductImage(card, currentIndex + delta);
}

function renderModalGallery(product) {
    const imgs = productImages(product);
    const main = $('modal-img');
    const thumbs = $('modal-thumbs');

    main.src = imgs[0];
    thumbs.replaceChildren();
    thumbs.hidden = imgs.length <= 1;

    if (imgs.length <= 1) return;

    imgs.forEach((src, index) => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = `product-modal__thumb${index === 0 ? ' active' : ''}`;
        btn.setAttribute('aria-label', `Ver imagen ${index + 1}`);
        btn.dataset.src = src;

        const img = document.createElement('img');
        img.src = src;
        img.alt = '';
        img.loading = 'lazy';

        btn.appendChild(img);
        btn.onclick = () => {
            main.src = src;
            thumbs.querySelectorAll('.product-modal__thumb').forEach((thumb) => thumb.classList.remove('active'));
            btn.classList.add('active');
        };
        thumbs.appendChild(btn);
    });
}

const COLOR_MAP = {
    negro: '#1a1a1a',
    blanco: '#f5f5f0',
    azul: '#2f4a6e',
    celeste: '#8eb4c8',
    gris: '#9a9a9a',
    beige: '#d4c4a8',
    marron: '#6b4423',
    marrón: '#6b4423',
    rosa: '#e8b4b8',
    verde: '#4a6741',
    rojo: '#8b2e2e',
    denim: '#3d5a80',
    crudo: '#e8e0d0',
};

function parseSizesList(value) {
    if (!value || typeof value !== 'string') return [];
    const trimmed = value.trim();
    const parts = trimmed.includes(',')
        ? trimmed.split(',')
        : trimmed.split(/\s+/);
    return [...new Set(parts.map((s) => s.trim().toUpperCase()).filter(Boolean))];
}

function parseColorsList(value) {
    if (!value || typeof value !== 'string') return [];
    return [...new Set(
        value.split(/[,;|/]+/).map((s) => s.trim().toLowerCase()).filter(Boolean)
    )];
}

function parseList(value) {
    return parseSizesList(value);
}

function resolveColor(value) {
    const key = value.toLowerCase();
    return COLOR_MAP[key] || (key.startsWith('#') ? key : key);
}

function parseSizeStockMap(product) {
    const sizes = parseList(product.sizes);
    const map = {};

    if (product.size_stock) {
        const raw = product.size_stock.trim();
        try {
            const parsed = JSON.parse(raw);
            if (parsed && typeof parsed === 'object') {
                Object.entries(parsed).forEach(([k, v]) => {
                    map[k.trim().toUpperCase()] = Math.max(0, Number(v) || 0);
                });
                return map;
            }
        } catch {
            /* formato S:4, M:0 */
        }
        raw.split(/[,;]+/).forEach((part) => {
            const [size, qty] = part.split(':').map((s) => s.trim());
            if (size) map[size.toUpperCase()] = Math.max(0, Number(qty) || 0);
        });
        if (Object.keys(map).length) return map;
    }

    const fallback = Math.max(0, Number(product.stock) || 0);
    sizes.forEach((s) => {
        map[s.toUpperCase()] = fallback;
    });
    return map;
}

function getTotalAvailableStock(stockMap) {
    return Object.values(stockMap).reduce((sum, n) => sum + n, 0);
}

function renderModalSizes(product) {
    const container = $('sizes-container');
    const hint = $('size-hint');
    container.replaceChildren();
    hint.textContent = '';
    selectedSize = null;
    selectedSizeMaxQty = 0;

    const sizes = parseSizesList(product.sizes);
    const stockMap = parseSizeStockMap(product);

    if (!sizes.length) {
        container.innerHTML = '<p class="product-modal__hint">Consultá disponibilidad por WhatsApp</p>';
        return;
    }

    sizes.forEach((size) => {
        const qty = stockMap[size] ?? 0;
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'size-pill';
        btn.dataset.size = size;

        const label = document.createElement('span');
        label.className = 'size-pill__label';
        label.textContent = size;
        btn.appendChild(label);

        if (qty <= 0) {
            btn.classList.add('size-pill--out');
            btn.disabled = true;
            btn.setAttribute('aria-disabled', 'true');
            btn.setAttribute('aria-label', `Talle ${size}, agotado`);
        } else {
            // Mostrar cantidad si es baja (≤5), sino solo el talle
            if (qty <= 5) {
                const badge = document.createElement('span');
                badge.className = 'size-pill__badge';
                badge.textContent = `${qty} left`;
                btn.appendChild(badge);
            }
            btn.setAttribute('aria-label', `Talle ${size}, ${qty} disponibles`);
            btn.onclick = () => selectSize(btn, size, qty);
        }

        container.appendChild(btn);
    });
}

function renderModalColors(product) {
    const block = $('colors-block');
    const container = $('colors-container');
    const colors = parseColorsList(product.colors);

    container.replaceChildren();
    selectedColor = null;

    if (!colors.length) {
        block.hidden = true;
        return;
    }

    block.hidden = false;
    colors.forEach((color) => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'color-swatch';
        btn.dataset.color = color;
        btn.style.setProperty('--swatch', resolveColor(color));
        btn.setAttribute('aria-label', `Color ${color}`);
        btn.onclick = () => selectColor(btn, color);
        container.appendChild(btn);
    });
}

function updateModalStockLine(product) {
    const stockMap = parseSizeStockMap(product);
    const total = getTotalAvailableStock(stockMap);
    const el = $('modal-stock');

    if (total <= 0) {
        el.className = 'product-modal__stock product-modal__stock--out';
        el.textContent = 'Sin stock disponible';
        return;
    }

    el.className = 'product-modal__stock';
    el.textContent = `${total} unidades disponibles`;
}

function updateModalCta() {
    const btn = $('modal-add-btn');
    if (!selectedProduct) return;

    const sizes = parseSizesList(selectedProduct.sizes);
    const colors = parseColorsList(selectedProduct.colors);
    const needsSize = sizes.length > 0;
    const needsColor = colors.length > 0;
    const stockMap = parseSizeStockMap(selectedProduct);
    const hasStock = getTotalAvailableStock(stockMap) > 0;

    if (!hasStock) {
        btn.disabled = true;
        btn.textContent = 'Producto agotado';
        return;
    }

    if (needsSize && !selectedSize) {
        btn.disabled = true;
        btn.textContent = 'Seleccioná un talle';
        return;
    }

    if (needsColor && !selectedColor) {
        btn.disabled = true;
        btn.textContent = 'Seleccioná un color';
        return;
    }

    btn.disabled = false;
    btn.textContent = 'Agregar al carrito';
}

function openModal(id) {
    const p = products.find((x) => x.id === id);
    if (!p) return;

    selectedProduct = p;
    selectedSize = null;
    selectedColor = null;
    selectedSizeMaxQty = 0;

    $('modal-name').textContent = p.name;
    $('modal-desc').textContent = p.description;

    // Precio con descuento
    const discount = p.discount || 0;
    const priceEl = $('modal-price');
    if (discount > 0) {
        const discounted = (p.price * (1 - discount / 100)).toFixed(2);
        priceEl.innerHTML = `<span style="font-size:1.5rem;font-weight:700">€${discounted}</span> <span style="text-decoration:line-through;color:#aaa;font-size:1rem;font-weight:400">€${p.price.toFixed(2)}</span> <span style="background:#ef4444;color:#fff;font-size:0.72rem;font-weight:700;padding:2px 7px;border-radius:4px;vertical-align:middle">-${discount}%</span>`;
    } else {
        priceEl.textContent = formatPrice(p.price);
    }
    renderModalGallery(p);
    $('modal-qty').value = 1;
    $('size-hint').textContent = '';

    renderModalSizes(p);
    renderModalColors(p);
    updateModalStockLine(p);
    updateModalCta();

    const modal = $('product-modal');
    modal.hidden = false;
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    const modal = $('product-modal');
    modal.hidden = true;
    modal.style.display = 'none';
    document.body.style.overflow = '';
    closeImagePreview();
}

function openImagePreview(src) {
    $('preview-img').src = src;
    $('image-preview').classList.add('active');
}

function changeModalQty(delta) {
    const input = $('modal-qty');
    let qty = Number(input.value) || 1;
    const max = selectedSizeMaxQty > 0 ? selectedSizeMaxQty : 99;
    qty = Math.max(1, Math.min(max, qty + delta));
    input.value = qty;
}

function closeImagePreview() {
    $('image-preview').classList.remove('active');
}

function addToCartFromModal() {
    if (!selectedProduct || $('modal-add-btn').disabled) return;

    const sizes = parseSizesList(selectedProduct.sizes);
    const colors = parseColorsList(selectedProduct.colors);
    if (sizes.length && !selectedSize) {
        alert('Seleccioná un talle disponible');
        return;
    }
    if (colors.length && !selectedColor) {
        alert('Seleccioná un color');
        return;
    }

    const qty = parseInt($('modal-qty').value, 10) || 1;
    const itemKey = `${selectedProduct.id}-${selectedSize}-${selectedColor}`;

    const item = cart.find((i) => i.key === itemKey);
    if (item) {
        item.qty += qty;
    } else {
        cart.push({
            ...selectedProduct,
            qty,
            size: selectedSize,
            color: selectedColor,
            key: itemKey,
        });
    }

    updateCart();
    showToast();
    closeModal();
}

function selectSize(el, size, maxQty) {
    document.querySelectorAll('.size-pill:not(.size-pill--out)').forEach((b) => {
        b.classList.remove('active');
        b.setAttribute('aria-selected', 'false');
    });
    el.classList.add('active');
    el.setAttribute('aria-selected', 'true');
    selectedSize = size;
    selectedSizeMaxQty = maxQty;

    const input = $('modal-qty');
    if (Number(input.value) > maxQty) input.value = maxQty;

    const hint = $('size-hint');
    if (maxQty <= 3) {
        hint.textContent = `¡Solo quedan ${maxQty} en talle ${size}!`;
    } else if (maxQty <= 5) {
        hint.textContent = `Últimas ${maxQty} unidades en talle ${size}`;
    } else {
        hint.textContent = '';
    }

    updateModalCta();
}

function selectColor(el, color) {
    document.querySelectorAll('.color-swatch').forEach((c) => {
        c.classList.remove('active');
        c.setAttribute('aria-selected', 'false');
    });
    el.classList.add('active');
    el.setAttribute('aria-selected', 'true');
    selectedColor = color;
    updateModalCta();
}

function sortedCatalogProducts() {
    return [...products].sort((a, b) => {
        const aStock = getTotalAvailableStock(parseSizeStockMap(a));
        const bStock = getTotalAvailableStock(parseSizeStockMap(b));
        // Agotados al final
        if (aStock <= 0 && bStock > 0) return 1;
        if (aStock > 0 && bStock <= 0) return -1;
        // Entre los disponibles: destacados primero
        return Number(Boolean(b.is_featured)) - Number(Boolean(a.is_featured));
    });
}

function buildProductPriceHtml(p) {
    const discount = p.discount || 0;
    if (discount > 0) {
        const discounted = (p.price * (1 - discount / 100)).toFixed(2);
        return `<p class="product-price">
            <span class="product-price__new">€${discounted}</span>
            <span class="product-price__old">€${p.price.toFixed(2)}</span>
            <span class="product-price__badge">-${discount}%</span>
        </p>`;
    }

    return `<p class="product-price">${formatPrice(p.price)}</p>`;
}

function buildCarouselCard(p) {
    const imgs = productImages(p);
    const name = escapeHtml(p.name);
    const hasMultiple = imgs.length > 1;
    const dataImgs = hasMultiple ? `data-images="${escapeHtml(imgs.join(','))}"` : '';
    const discount = p.discount || 0;
    const isFeatured = p.is_featured || false;
    const stockMap = parseSizeStockMap(p);
    const totalStock = getTotalAvailableStock(stockMap);
    const isOutOfStock = totalStock <= 0;

    return [
        `<div class="carousel-card${isFeatured ? ' product--featured' : ''}${discount > 0 ? ' product--discount' : ''}${isOutOfStock ? ' product--out-of-stock' : ''}" data-product-id="${p.id}">`,
        isFeatured ? '<div class="product__featured-badge">Destacado</div>' : '',
        discount > 0 ? `<div class="product__discount-ribbon">-${discount}%</div>` : '',
        isOutOfStock ? '<div class="product__out-badge">Agotado</div>' : '',
        `<div class="product-img-wrap" ${dataImgs}>`,
        `<img class="product-img product-img--main" src="${escapeHtml(imgs[0])}" alt="${name}" loading="lazy">`,
        hasMultiple
            ? `<img class="product-img product-img--hover" src="${escapeHtml(imgs[1])}" alt="${name}" loading="lazy">`
            : '',
        hasMultiple ? `<span class="product-image-count">${imgs.length} fotos</span>` : '',
        `</div>`,
        '<div class="product-info">',
        `<h3>${name}</h3>`,
        buildProductPriceHtml(p),
        isOutOfStock
            ? '<button type="button" class="carousel-card__cta" disabled>Sin stock</button>'
            : '<button type="button" class="carousel-card__cta">Ver producto</button>',
        '</div>',
        '</div>',
    ].join('');
}

function buildProductCard(p) {
    const imgs = productImages(p);
    const name = escapeHtml(p.name);
    const desc = escapeHtml(p.description);
    const hasMultiple = imgs.length > 1;
    const dataImgs = hasMultiple ? `data-images="${escapeHtml(imgs.join(','))}"` : '';
    const discount = p.discount || 0;
    const isFeatured = p.is_featured || false;
    const stockMap = parseSizeStockMap(p);
    const totalStock = getTotalAvailableStock(stockMap);
    const isOutOfStock = totalStock <= 0;
    const priceHtml = buildProductPriceHtml(p);

    return [
        `<div id="product-${p.id}" class="product${isFeatured ? ' product--featured' : ''}${discount > 0 ? ' product--discount' : ''}${isOutOfStock ? ' product--out-of-stock' : ''}" data-product-id="${p.id}">`,
        isFeatured ? '<div class="product__featured-badge">⭐ Destacado</div>' : '',
        discount > 0 ? `<div class="product__discount-ribbon">-${discount}%</div>` : '',
        isOutOfStock ? '<div class="product__out-badge">Agotado</div>' : '',
        `<div class="product-img-wrap" ${dataImgs}>`,
        `<img class="product-img product-img--main" data-gallery-main src="${escapeHtml(imgs[0])}" alt="${name}" loading="lazy">`,
        hasMultiple ? `<img class="product-img product-img--hover" src="${escapeHtml(imgs[1])}" alt="${name}" loading="lazy">` : '',
        hasMultiple ? `<span class="product-image-count">${imgs.length} fotos</span>` : '',
        hasMultiple ? `<button type="button" class="product-gallery-nav product-gallery-nav--prev" data-action="gallery-prev" data-id="${p.id}" aria-label="Imagen anterior">‹</button>` : '',
        hasMultiple ? `<button type="button" class="product-gallery-nav product-gallery-nav--next" data-action="gallery-next" data-id="${p.id}" aria-label="Imagen siguiente">›</button>` : '',
        `</div>`,
        buildProductThumbs(imgs, p.id),
        '<div class="product-info">',
        `<h3>${name}</h3>`,
        priceHtml,
        isOutOfStock
            ? '<button type="button" disabled class="btn-out-of-stock">Sin stock</button>'
            : `<button type="button" data-action="add" data-id="${p.id}">Agregar</button>`,
        '</div>',
        `<p class="product-description">${desc}</p>`,
        '</div>',
    ].join('');
}

function loadProducts() {
    const grid = $('products');
    const carouselTrack = $('carousel-track');

    if (!products.length) {
        grid.innerHTML = '<p class="cart-empty">No hay productos disponibles por ahora.</p>';
        carouselTrack.innerHTML = '';
        return;
    }

    const orderedProducts = sortedCatalogProducts();
    const carouselHTML = orderedProducts.map(buildCarouselCard).join('');
    carouselTrack.innerHTML = carouselHTML + carouselHTML;
    grid.innerHTML = orderedProducts.map(buildProductCard).join('');

    if (!gridListenersBound) {
        grid.addEventListener('click', handleProductGridClick);
        carouselTrack.addEventListener('click', handleCarouselClick);
        carouselTrack.addEventListener('touchstart', pauseCarousel, { passive: true });
        carouselTrack.addEventListener('touchend', resumeCarousel, { passive: true });
        gridListenersBound = true;
    }
}

function handleProductGridClick(e) {
    const galleryBtn = e.target.closest('[data-action="gallery-prev"], [data-action="gallery-next"]');
    if (galleryBtn) {
        e.preventDefault();
        e.stopPropagation();
        stepProductImage(galleryBtn, galleryBtn.dataset.action === 'gallery-next' ? 1 : -1);
        return;
    }

    const thumbBtn = e.target.closest('[data-action="thumb"]');
    if (thumbBtn) {
        e.preventDefault();
        e.stopPropagation();
        selectProductThumb(thumbBtn);
        return;
    }

    const addBtn = e.target.closest('[data-action="add"]');
    if (addBtn) {
        e.stopPropagation();
        openModal(Number(addBtn.dataset.id));
        return;
    }
    const card = e.target.closest('.product[data-product-id]');
    if (card) toggleDetail(Number(card.dataset.productId));
}

function handleCarouselClick(e) {
    const card = e.target.closest('.carousel-card[data-product-id]');
    if (card) openModal(Number(card.dataset.productId));
}

function pauseCarousel() {
    $('carousel-track').classList.add('paused');
}

function resumeCarousel() {
    setTimeout(() => $('carousel-track').classList.remove('paused'), 1000);
}

function toggleCart() {
    const isOpen = $('cart').classList.toggle('active');
    $('cart-overlay').classList.toggle('active');
    document.querySelector('.main-nav')?.classList.remove('active');
    $('cart-overlay').setAttribute('aria-hidden', String(!isOpen));
    updateCart();
}

function toggleMenu() {
    const nav = document.querySelector('.main-nav');
    const menuBtn = document.querySelector('.menu-toggle');
    const isOpen = nav.classList.toggle('active');
    menuBtn?.setAttribute('aria-expanded', String(isOpen));
}

function toggleDetail(id) {
    document.getElementById(`product-${id}`)?.classList.toggle('show-description');
}

function showToast() {
    const t = $('toast');
    t.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.remove('show'), 2000);
}

function buildCartItemHtml(item) {
    const key = escapeHtml(item.key);
    const discount = itemDiscount(item);
    const unitFinal = itemFinalUnitPrice(item);
    const lineOriginal = Number(item.price) * item.qty;
    const lineFinal = unitFinal * item.qty;
    const priceHtml = discount > 0
        ? `<span class="cart-item__price cart-item__price--discount">
            <span class="cart-item__old-price">${formatPrice(lineOriginal)}</span>
            <strong>${formatPrice(lineFinal)}</strong>
            <em>-${discount}%</em>
        </span>`
        : `<span class="cart-item__price">${formatPrice(lineFinal)}</span>`;

    return [
        '<div class="cart-item">',
        '<div>',
        `<strong>${escapeHtml(item.name)}</strong>`,
        `<span>Talle: ${escapeHtml(item.size || 'N/A')}</span>`,
        `<span>Color: ${escapeHtml(item.color || 'N/A')}</span>`,
        `<span>Cantidad: ${item.qty}</span>`,
        discount > 0 ? `<span class="cart-item__discount-note">Descuento aplicado: ${discount}%</span>` : '',
        '</div>',
        '<div class="qty">',
        `<button type="button" data-qty="${key}" data-delta="-1" aria-label="Reducir">−</button>`,
        `<span>${item.qty}</span>`,
        `<button type="button" data-qty="${key}" data-delta="1" aria-label="Aumentar">+</button>`,
        '</div>',
        priceHtml,
        '</div>',
    ].join('');
}

function updateCart() {
    const container = $('cart-items');
    const count = $('cart-count');
    const subtitle = $('cart-subtitle');

    let subtotal = 0;

    if (!cart.length) {
        container.innerHTML =
            '<p class="cart-empty">Tu carrito está vacío. Agrega algo lindo para comenzar.</p>';
    } else {
        const rows = [];
        cart.forEach((item) => {
            subtotal += itemFinalUnitPrice(item) * item.qty;
            rows.push(buildCartItemHtml(item));
        });
        container.innerHTML = rows.join('');

        container.querySelectorAll('[data-qty]').forEach((btn) => {
            btn.addEventListener('click', () => {
                changeQty(btn.dataset.qty, Number(btn.dataset.delta));
            });
        });
    }

    const finalTotal = subtotal + shippingPrice;

    $('total').innerHTML = [
        '<div class="cart-summary">',
        `<div class="summary-row"><span>Subtotal</span><span>${formatPrice(subtotal)}</span></div>`,
        `<div class="summary-row"><span>Envío</span><span>${shippingPrice > 0 ? formatPrice(shippingPrice) : 'Pendiente'}</span></div>`,
        '<div class="summary-divider"></div>',
        `<div class="summary-total"><span>Total</span><span>${formatPrice(finalTotal)}</span></div>`,
        '</div>',
    ].join('');

    const totalQty = cart.reduce((sum, item) => sum + item.qty, 0);
    count.textContent = totalQty;
    subtitle.textContent = `${cart.length} artículo${cart.length === 1 ? '' : 's'}`;

    // Mostrar/ocultar botón vaciar
    const clearBtn = $('cart-clear-btn');
    if (clearBtn) clearBtn.style.display = cart.length ? 'flex' : 'none';

    saveCart();
}

function saveCart() {
    localStorage.setItem('cart', JSON.stringify(cart));
}

function loadCart() {
    const isFirstLoad = !localStorage.getItem('cartInitialized');
    if (isFirstLoad) {
        cart = [];
        localStorage.setItem('cartInitialized', 'true');
    } else {
        try {
            const data = localStorage.getItem('cart');
            const parsed = data ? JSON.parse(data) : [];
            cart = Array.isArray(parsed) ? parsed : [];
        } catch {
            cart = [];
        }
    }
    updateCart();
}

function changeQty(key, delta) {
    const item = cart.find((i) => i.key === key);
    if (!item) return;

    item.qty += delta;
    if (item.qty <= 0) {
        cart = cart.filter((i) => i.key !== key);
    }
    updateCart();
}

function clearCart() {
    if (!cart.length) return;
    if (!confirm('¿Vaciar el carrito?')) return;
    cart = [];
    shippingPrice = 0;
    updateCart();
}

async function checkout() {
    if (!cart.length) {
        alert('El carrito está vacío. Agrega algún producto antes de pagar.');
        return;
    }

    const btn = document.querySelector('.checkout-btn');
    btn.disabled = true;

    try {
        const res = await fetch('/checkout/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(cart),
        });
        const data = await res.json();

        if (res.ok && data.payment_url) {
            window.location.href = data.payment_url;
        } else {
            alert(data.detail || 'No se pudo procesar el pago.');
        }
    } catch {
        alert('Error de conexión. Intenta de nuevo.');
    } finally {
        btn.disabled = false;
    }
}

function openShippingModal() {
    const modal = $('shipping-modal');
    modal.hidden = false;
    modal.classList.add('active');
}

function closeShippingModal() {
    const modal = $('shipping-modal');
    modal.hidden = true;
    modal.classList.remove('active');
}

// ── Tarifas de envío por zona postal (España peninsular + islas) ──
// Basado en tarifas de referencia de Correos España
// El prefijo de 2 dígitos del CP determina la provincia/zona
const SHIPPING_ZONES = {
    // Zona 0 — Alicante (origen) — ENVÍO GRATIS
    locker:  { z0: 0, z1: 3.95, z2: 4.95, z3: 5.95, z4: 7.95, z5: 9.95, z6: 14.95 },
    pickup:  { z0: 0, z1: 4.95, z2: 5.95, z3: 6.95, z4: 8.95, z5: 11.95, z6: 16.95 },
};

const CP_ZONE = {
    // Zona 0 — Alicante (envío gratis, origen)
    '03': 'z0',
    // Zona 1 — Comunidad Valenciana
    '46': 'z1', '12': 'z1',
    // Zona 2 — Murcia, Almería, Albacete
    '30': 'z2', '04': 'z2', '02': 'z2',
    // Zona 3 — Madrid, Castilla-La Mancha, Andalucía
    '28': 'z3', '29': 'z3', '14': 'z3', '41': 'z3', '45': 'z3', '16': 'z3',
    '13': 'z3', '19': 'z3', '18': 'z3', '23': 'z3', '11': 'z3',
    // Zona 4 — Cataluña, Aragón, Castilla y León, Extremadura
    '08': 'z4', '17': 'z4', '43': 'z4', '25': 'z4', '50': 'z4', '22': 'z4',
    '44': 'z4', '40': 'z4', '42': 'z4', '47': 'z4', '49': 'z4', '37': 'z4',
    '34': 'z4', '24': 'z4', '09': 'z4', '05': 'z4', '06': 'z4', '10': 'z4',
    '21': 'z4',
    // Zona 5 — Norte (Galicia, Asturias, Cantabria, País Vasco, Navarra, La Rioja)
    '15': 'z5', '27': 'z5', '32': 'z5', '36': 'z5', '33': 'z5', '39': 'z5',
    '48': 'z5', '20': 'z5', '01': 'z5', '31': 'z5', '26': 'z5',
    // Zona 6 — Islas Baleares, Canarias, Ceuta, Melilla
    '07': 'z6', '35': 'z6', '38': 'z6', '51': 'z6', '52': 'z6',
};

const ZONE_LABELS = {
    z0: 'Alicante (origen)',
    z1: 'Comunidad Valenciana',
    z2: 'Sureste peninsular',
    z3: 'Centro y sur peninsular',
    z4: 'Resto de la península',
    z5: 'Norte de España',
    z6: 'Islas / Ceuta / Melilla',
};

function getZoneFromPostal(cp) {
    const prefix = String(cp).trim().slice(0, 2);
    return CP_ZONE[prefix] || 'z4';
}

function calculateShipping() {
    const city   = $('destination-city').value.trim();
    const postal = $('postal-code').value.trim();
    const type   = $('shipping-type').value;

    if (!city || !postal) {
        $('shipping-result').innerHTML = '<p style="color:#ef4444;font-size:0.85rem;margin-top:12px;">Completa el destino y el código postal.</p>';
        return;
    }

    if (!/^\d{5}$/.test(postal)) {
        $('shipping-result').innerHTML = '<p style="color:#ef4444;font-size:0.85rem;margin-top:12px;">El código postal debe tener 5 dígitos.</p>';
        return;
    }

    const zone  = getZoneFromPostal(postal);
    const price = SHIPPING_ZONES[type][zone];
    const isFree = price === 0;
    const deliveryLabel = type === 'locker' ? 'Locker InPost' : 'Punto de recogida';
    const zoneLabel = ZONE_LABELS[zone];
    const days = zone === 'z0' ? 'Entrega local' : zone === 'z6' ? '3-5 días' : '24-48h';

    shippingPrice = price;
    updateCart();

    $('shipping-result').innerHTML = `
        <div class="shipping-result-box">
            <div class="shipping-result-row">
                <span>Destino</span>
                <strong>${escapeHtml(city)} (${escapeHtml(postal)})</strong>
            </div>
            <div class="shipping-result-row">
                <span>Zona</span>
                <strong>${zoneLabel}</strong>
            </div>
            <div class="shipping-result-row">
                <span>Tipo</span>
                <strong>${deliveryLabel}</strong>
            </div>
            <div class="shipping-result-row">
                <span>Plazo estimado</span>
                <strong>${days}</strong>
            </div>
            <div class="shipping-result-total ${isFree ? 'shipping-result-total--free' : ''}">
                <span>Coste de envío</span>
                <strong>${isFree ? '¡GRATIS!' : formatPrice(price)}</strong>
            </div>
            <p class="shipping-result-note">
                Precios de referencia basados en tarifas de Correos España · IVA incluido · Paquete hasta 1kg
            </p>
        </div>`;

    $('shipping-reset-btn').style.display = 'inline-flex';
}

function resetShipping() {
    $('destination-city').value = '';
    $('postal-code').value = '';
    $('shipping-type').value = 'locker';
    $('shipping-result').innerHTML = '';
    shippingPrice = 0;
    updateCart();
    $('shipping-reset-btn').style.display = 'none';
    $('destination-city').focus();
}

function openRatesModal() {
    const m = $('rates-modal');
    // Mover al body para evitar problemas de stacking context
    if (m.parentElement !== document.body) {
        document.body.appendChild(m);
    }
    m.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeRatesModal() {
    $('rates-modal').classList.remove('active');
    document.body.style.overflow = '';
}

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeModal();
        closeImagePreview();
        closeShippingModal();
        closeRatesModal();
        if ($('cart').classList.contains('active')) toggleCart();
    }
});

document.addEventListener('DOMContentLoaded', async () => {
    loadCart();

    // ── Contenido dinámico (topbar + social + reviews + footer) ──
    // Hero y About ya se renderizan desde el servidor (Jinja2).
    // El fetch solo actualiza topbar, redes sociales y reviews.
    fetch('/admin/content/data')
        .then(r => r.ok ? r.json() : null)
        .then(data => {
            if (!data) return;

            // ── Reviews ───────────────────────────────────────────
            if (data.reviews?.images?.length) {
                const container = document.getElementById('reviews-container');
                if (container) {
                    container.innerHTML = data.reviews.images
                        .map((url, i) => `<div class="review"><img src="${url}" alt="Opinión de cliente ${i + 1}" loading="lazy"></div>`)
                        .join('');
                }
            }

            // ── Topbar ────────────────────────────────────────────
            const tb = data.topbar;
            if (tb) {
                const track = document.getElementById('topbar-track');
                if (track && tb.items?.length) {
                    const socialHtml = _buildTopbarSocial(data.social);
                    const sep = '<span class="topbar__sep">·</span>';
                    const itemsHtml = tb.items.map(t =>
                        `<span class="topbar__item">${escapeHtml(t)}</span>`
                    ).join(sep);
                    const emailHtml = tb.contact_email
                        ? `${sep}<span class="topbar__item">📩 ${escapeHtml(tb.contact_email)}</span>`
                        : '';
                    const waHtml = (tb.whatsapp_number && tb.whatsapp_display)
                        ? `${sep}<span class="topbar__item">💬 WhatsApp: <a href="https://wa.me/${escapeHtml(tb.whatsapp_number)}" target="_blank" rel="noopener noreferrer" class="topbar__link">${escapeHtml(tb.whatsapp_display)}</a></span>`
                        : '';
                    const socialSlot = socialHtml
                        ? `${sep}<span class="topbar__item">Síguenos ${socialHtml}</span>`
                        : '';
                    const full = itemsHtml + emailHtml + waHtml + socialSlot;
                    track.innerHTML = full + sep + full;
                }

                // Email en footer
                if (tb.contact_email) {
                    const el = document.getElementById('footer-email');
                    if (el) { el.href = `mailto:${tb.contact_email}`; el.textContent = tb.contact_email; }
                }
                // WhatsApp footer + flotante
                if (tb.whatsapp_number) {
                    const waUrl = `https://wa.me/${tb.whatsapp_number}`;
                    const footerWa = document.getElementById('footer-whatsapp');
                    if (footerWa) footerWa.href = waUrl;
                    const floatWa = document.getElementById('whatsapp-float');
                    if (floatWa) floatWa.href = waUrl;
                }
            }

            // ── Social links (footer) ─────────────────────────────
            if (data.social && Object.keys(data.social).length) {
                const container = document.getElementById('footer-social-links');
                if (container) {
                    container.innerHTML = _buildFooterSocial(data.social);
                }
            }
        })
        .catch(() => {});

    // ── Analytics: pageview ──────────────────────────────────────
    fetch('/analytics/pageview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            path: window.location.pathname,
            referrer: document.referrer || null,
        }),
    }).catch(() => {});

    // ── Analytics: click tracking ────────────────────────────────
    document.addEventListener('click', (e) => {
        const xPct = Math.round((e.clientX / window.innerWidth) * 100);
        const yPct = Math.round(((e.clientY + window.scrollY) / document.body.scrollHeight) * 100);

        // Clic en tarjeta de producto
        const card = e.target.closest('[data-product-id]');
        if (card) {
            const pid = Number(card.dataset.productId);
            const p = products.find(x => x.id === pid);
            fetch('/analytics/click', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    element: 'product-card',
                    label: p?.name || null,
                    product_id: pid,
                    x_pct: xPct,
                    y_pct: yPct,
                }),
            }).catch(() => {});
            return;
        }

        // Clic en agregar al carrito
        const addBtn = e.target.closest('[data-action="add"]');
        if (addBtn) {
            fetch('/analytics/click', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    element: 'add-to-cart',
                    x_pct: xPct,
                    y_pct: yPct,
                }),
            }).catch(() => {});
            return;
        }

        // Clic en carrito
        if (e.target.closest('.cart-icon')) {
            fetch('/analytics/click', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ element: 'cart-icon', x_pct: xPct, y_pct: yPct }),
            }).catch(() => {});
        }
    }, { passive: true });

    try {
        const response = await fetch('/products/');
        if (!response.ok) throw new Error('Products fetch failed');
        products = await response.json();
        loadProducts();
        updateCart();
    } catch (error) {
        console.error('Error loading products:', error);
        $('products').innerHTML = '<p class="cart-empty">No se pudieron cargar los productos.</p>';
    }
});

// ── LUPA DE DETALLE (lens zoom) ──────────────────────────────
(function initZoomLens() {
    const ZOOM = 2.8; // factor de ampliación
    const LENS_SIZE = 90;

    const wrap = document.getElementById('modal-img-wrap');
    const lens = document.getElementById('zoom-lens');
    const result = document.getElementById('zoom-result');

    if (!wrap || !lens || !result) return;

    function getImg() {
        return document.getElementById('modal-img');
    }

    function updateZoom(e) {
        const img = getImg();
        if (!img || !img.complete) return;

        const rect     = img.getBoundingClientRect();
        const wrapRect = wrap.getBoundingClientRect();

        // Posición del cursor relativa al wrap (para la lupa)
        const halfLens = LENS_SIZE / 2;
        let lx = e.clientX - wrapRect.left;
        let ly = e.clientY - wrapRect.top;
        lx = Math.max(halfLens, Math.min(wrapRect.width  - halfLens, lx));
        ly = Math.max(halfLens, Math.min(wrapRect.height - halfLens, ly));

        lens.style.left = (lx - halfLens) + 'px';
        lens.style.top  = (ly - halfLens) + 'px';

        // Panel de resultado: sigue el cursor en viewport (fixed)
        const RW = 240, RH = 240;
        const margin = 16;
        let rx = e.clientX + margin;
        let ry = e.clientY - RH / 2;

        // Evitar que se salga de la pantalla
        if (rx + RW > window.innerWidth)  rx = e.clientX - RW - margin;
        if (ry < margin)                  ry = margin;
        if (ry + RH > window.innerHeight) ry = window.innerHeight - RH - margin;

        result.style.left = rx + 'px';
        result.style.top  = ry + 'px';

        // Calcular zoom del background
        const scaleX = img.naturalWidth  / rect.width;
        const scaleY = img.naturalHeight / rect.height;

        const imgX = (e.clientX - rect.left) * scaleX;
        const imgY = (e.clientY - rect.top)  * scaleY;

        const bgX = -(imgX * ZOOM - RW / 2);
        const bgY = -(imgY * ZOOM - RH / 2);

        result.style.backgroundImage    = `url('${img.src}')`;
        result.style.backgroundSize     = `${img.naturalWidth * ZOOM}px ${img.naturalHeight * ZOOM}px`;
        result.style.backgroundPosition = `${bgX}px ${bgY}px`;
    }

    wrap.addEventListener('mousemove', updateZoom);

    // Ocultar lupa cuando el cursor sale del wrap
    wrap.addEventListener('mouseleave', () => {
        lens.style.display  = 'none';
        result.style.display = 'none';
    });

    wrap.addEventListener('mouseenter', () => {
        lens.style.display  = 'block';
        result.style.display = 'block';
    });

    // Re-inicializar cuando cambia la imagen (thumbnails)
    const observer = new MutationObserver(() => {
        const img = getImg();
        if (img) {
            result.style.backgroundImage = `url('${img.src}')`;
        }
    });

    const imgEl = getImg();
    if (imgEl) {
        observer.observe(imgEl, { attributes: true, attributeFilter: ['src'] });
    }
})();
