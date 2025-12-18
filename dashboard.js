// проверка авторизации
const token = localStorage.getItem("token");
if (!token) {
    window.location.href = "index.html";
}

// выход
document.getElementById("logoutBtn").addEventListener("click", () => {
    localStorage.removeItem("token");
    window.location.href = "index.html";
});

// получение данных пользователя
async function fetchUserData() {
    try {
        const response = await fetch("/users/me", {
            headers: { "Authorization": `Bearer ${token}` }
        });
        if (!response.ok) {
            throw new Error("Ошибка при получении данных пользователя");
        }
        return await response.json();
    } catch (error) {
        console.error("Error:", error);
        alert("Ошибка при загрузке данных. Пожалуйста, войдите снова.");
        localStorage.removeItem("token");
        window.location.href = "index.html";
    }
}

// задания для учителя
async function loadTeacherAssignments() {
    try {
        const response = await fetch("/assignments", {
            headers: { "Authorization": `Bearer ${token}` }
        });
        if (!response.ok) throw new Error("Ошибка загрузки заданий");
        const assignments = await response.json();
        const assignmentsList = document.getElementById("assignmentsList");
        
        assignmentsList.innerHTML = assignments.map(assignment => `
            <div class="assignment">
                <h3>${assignment.title}</h3>
                <p>${assignment.description}</p>
                <button onclick="viewAssignmentAnswers(${assignment.id})">Просмотреть ответы</button>
            </div>
        `).join("");
    } catch (error) {
        console.error("Error:", error);
        alert("Ошибка при загрузке заданий");
    }
}

// заданиz для студента
async function loadStudentTasks() {
    try {
        const response = await fetch("/my-assignments", {
            headers: { "Authorization": `Bearer ${token}` }
        });
        if (!response.ok) throw new Error("Ошибка загрузки заданий");
        const tasks = await response.json();
        const tasksList = document.getElementById("tasksList");
        
        tasksList.innerHTML = tasks.map(task => `
            <div class="task">
                <h3>${task.title}</h3>
                <p>${task.description}</p>
                <button onclick="submitAnswer(${task.id})">Отправить ответ</button>
            </div>
        `).join("");
    } catch (error) {
        console.error("Error:", error);
        alert("Ошибка при загрузке заданий");
    }
}

// интерфейс
async function loadDashboard() {
    try {
        const user = await fetchUserData();
        
        if (user.is_teacher) {
            document.getElementById("teacherPanel").style.display = "block";
            await loadTeacherAssignments();
        } else {
            document.getElementById("studentPanel").style.display = "block";
            await loadStudentTasks();
        }
    } catch (error) {
        console.error("Error:", error);
        alert("Ошибка при загрузке данных");
    }
}

loadDashboard();