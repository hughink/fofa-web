// 等待 DOM 内容加载完毕后执行
document.addEventListener('DOMContentLoaded', () => {
    // 侧边栏切换按钮
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('overlay');

    // 切换侧边栏显示状态
    sidebarToggle.addEventListener('click', () => {
        sidebar.classList.toggle('is-hidden');
        overlay.classList.toggle('is-active');
    });

    // 点击覆盖层时隐藏侧边栏
    if (overlay) {
        overlay.addEventListener('click', () => {
            sidebar.classList.add('is-hidden');
            overlay.classList.remove('is-active');
        });
    }

    // 删除通知按钮功能
    const deleteButtons = document.querySelectorAll('.notification .delete');
    deleteButtons.forEach(button => {
        button.addEventListener('click', () => {
            button.parentElement.classList.add('is-hidden'); // 隐藏通知
        });
    });

    // Navbar 菜单按钮功能（移动端）
    const navbarBurgers = Array.from(document.querySelectorAll('.navbar-burger'));
    navbarBurgers.forEach(el => {
        el.addEventListener('click', () => {
            const target = el.dataset.target;
            const targetElement = document.getElementById(target);

            el.classList.toggle('is-active');
            targetElement.classList.toggle('is-active');
        });
    });
});
