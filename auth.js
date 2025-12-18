// Переключение между формами входа и регистрации
document.getElementById("registerLink").addEventListener("click", (e) => {
    e.preventDefault();
    document.getElementById("loginForm").style.display = "none";
    document.getElementById("registerForm").style.display = "block";
});

document.getElementById("loginLink").addEventListener("click", (e) => {
    e.preventDefault();
    document.getElementById("loginForm").style.display = "block";
    document.getElementById("registerForm").style.display = "none";
});

// Вход
document.getElementById("loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    const response = await fetch("/token", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: `username=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`
    });

    if (response.ok) {
        const data = await response.json();
        localStorage.setItem("token", data.access_token);
        window.location.href = "dashboard.html"; // Переход в личный кабинет
    } else {
        alert("Ошибка входа. Проверьте email и пароль.");
    }
});

// Регистрация
document.getElementById("signupForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("regEmail").value;
    const password = document.getElementById("regPassword").value;
    const isTeacher = document.getElementById("isTeacher").checked;

    const response = await fetch("/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, is_teacher: isTeacher })
    });

    if (response.ok) {
        alert("Регистрация успешна! Теперь войдите.");
        document.getElementById("loginForm").style.display = "block";
        document.getElementById("registerForm").style.display = "none";
    } else {
        alert("Ошибка регистрации. Возможно, email уже занят.");
    }
});