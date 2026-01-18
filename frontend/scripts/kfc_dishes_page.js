// 初始化
let totalPrice = 0;
const traySlots = document.getElementById('tray-slots');
const priceDisplay = document.getElementById('total-price');
const npcText = document.getElementById('npc-text');
const npcSprite = document.getElementById('npc-sprite');
const trayBar = document.getElementById('tray-bar');

// NPC 语录库
const phrases = {
    meat: ["Finger lickin' good!", "Protein power!", "Excellent choice!"],
    drink: ["So refreshing!", "Slurp slurp!", "Ice cold!"],
    side: ["Crispy!", "Good side dish!", "Yummy!"],
    diet: ["On a diet?", "Where is the meat?", "Healthy... I guess."],
    full: ["Whoa! That's a lot!", "Big eater!", "Careful now!"]
};

// 点击菜品触发
function orderItem(card) {
    const name = card.getAttribute('data-name');
    const price = parseInt(card.getAttribute('data-price'));
    const type = card.getAttribute('data-type');
    const imgSource = card.querySelector('.food-img').src;

    // 1. NPC 反应
    triggerNPCReaction(type);

    // 2. 执行抛物线动画
    animateFlyingFood(card, imgSource, () => {
        // 3. 动画结束后：添加到餐盘
        addItemToTray(imgSource);
        updateTotal(price);
    });
}

// 核心：飞行抛物线逻辑
function animateFlyingFood(startElem, imgSrc, onComplete) {
    // 获取起始位置 (卡片图片的位置)
    const startRect = startElem.querySelector('.food-img').getBoundingClientRect();
    // 获取终点位置 (餐盘中间)
    const endRect = traySlots.getBoundingClientRect();

    // 创建克隆体
    const flyer = document.createElement('img');
    flyer.src = imgSrc;
    flyer.classList.add('flying-food');
    
    // 初始位置设置
    flyer.style.top = `${startRect.top}px`;
    flyer.style.left = `${startRect.left}px`;
    flyer.style.width = `${startRect.width}px`;
    
    document.body.appendChild(flyer);

    // 强制浏览器重绘 (Reflow) 以确保初始位置生效
    void flyer.offsetWidth;

    // 计算终点坐标 (随机一点点偏移，让堆叠看起来自然)
    const targetTop = endRect.top + 10;
    const targetLeft = endRect.left + (Math.random() * (endRect.width - 50));

    // 设置 CSS 过渡目标
    flyer.style.top = `${targetTop}px`;
    flyer.style.left = `${targetLeft}px`;
    flyer.style.transform = `scale(0.5) rotate(${Math.random() * 360}deg)`; // 飞行中变小并旋转

    // 监听过渡结束
    flyer.addEventListener('transitionend', () => {
        flyer.remove(); // 移除飞行元素
        onComplete();   // 回调函数
    }, { once: true }); // 确保只触发一次
}

// 添加到下方餐盘 UI
function addItemToTray(imgSrc) {
    // 移除 "Empty" 提示
    const emptyMsg = traySlots.querySelector('.empty-msg');
    if (emptyMsg) emptyMsg.remove();

    // 创建小图标
    const item = document.createElement('img');
    item.src = imgSrc;
    item.classList.add('tray-item');
    traySlots.appendChild(item);
    
    // 自动滚动到最新物品
    traySlots.scrollLeft = traySlots.scrollWidth;

    // 触发餐盘抖动动画
    trayBar.classList.remove('tray-bounce');
    void trayBar.offsetWidth; // 触发重绘
    trayBar.classList.add('tray-bounce');
}

// 更新总价
function updateTotal(price) {
    totalPrice += price;
    priceDisplay.textContent = totalPrice;

    // 简单的价格颜色反馈
    const totalElem = priceDisplay.parentElement;
    totalElem.style.color = "#e76e55"; // 闪一下红色
    setTimeout(() => { totalElem.style.color = "inherit"; }, 200);
}

// NPC 互动逻辑
function triggerNPCReaction(type) {
    // 随机选一句话
    const list = phrases[type] || phrases['meat'];
    const text = list[Math.floor(Math.random() * list.length)];
    
    npcText.textContent = text;
    
    // 视觉反馈：上校震动一下
    npcSprite.classList.add('npc-excited');
    setTimeout(() => {
        npcSprite.classList.remove('npc-excited');
    }, 600);
}