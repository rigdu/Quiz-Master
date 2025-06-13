// static/app.js
console.log("Quiz App JS loaded successfully.");


document.getElementById('uploadForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const fileInput = document.getElementById('quizFile');
  const formData = new FormData();
  formData.append('file', fileInput.files[0]);

  const response = await fetch('/upload', {
    method: 'POST',
    body: formData
  });

  const result = await response.json();
  if (result.success) {
    alert(`✅ File uploaded. ${result.questions.length} questions loaded.`);
    // You can now call fetchQuestions() here to load into UI
  } else {
    alert(`❌ Upload failed: ${result.error}`);
  }
});
