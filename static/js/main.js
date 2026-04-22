// Main JavaScript File

// Mobile Menu Toggle
document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu toggle
    const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
    const navLinks = document.querySelector('.nav-links');
    
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', () => {
            navLinks.classList.toggle('active');
            mobileMenuBtn.innerHTML = navLinks.classList.contains('active') 
                ? '<i class="fas fa-times"></i>' 
                : '<i class="fas fa-bars"></i>';
        });
    }
    
    // Close flash messages
    document.querySelectorAll('.close-flash').forEach(button => {
        button.addEventListener('click', function() {
            this.parentElement.style.opacity = '0';
            setTimeout(() => {
                this.parentElement.remove();
            }, 300);
        });
    });
    
    // Auto-hide flash messages after 5 seconds
    setTimeout(() => {
        document.querySelectorAll('.flash-message').forEach(message => {
            message.style.opacity = '0';
            setTimeout(() => message.remove(), 300);
        });
    }, 5000);
    
    // Add animation classes to elements
    addAnimations();
    
    // Initialize tooltips
    initTooltips();
});

// Add animations to elements on scroll
function addAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // Observe all cards and sections
    document.querySelectorAll('.card, .stat-card, .section').forEach(el => {
        observer.observe(el);
    });
}

// Initialize tooltips
function initTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    
    tooltips.forEach(el => {
        el.addEventListener('mouseenter', function(e) {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = this.getAttribute('data-tooltip');
            document.body.appendChild(tooltip);
            
            const rect = this.getBoundingClientRect();
            tooltip.style.left = rect.left + rect.width / 2 - tooltip.offsetWidth / 2 + 'px';
            tooltip.style.top = rect.top - tooltip.offsetHeight - 10 + 'px';
            
            this._tooltip = tooltip;
        });
        
        el.addEventListener('mouseleave', function() {
            if (this._tooltip) {
                this._tooltip.remove();
                delete this._tooltip;
            }
        });
    });
}

// Quiz functionality
function submitQuiz(formId) {
    const form = document.getElementById(formId);
    const formData = new FormData(form);
    const answers = {};
    
    formData.forEach((value, key) => {
        if (key.startsWith('q_')) {
            answers[key.replace('q_', '')] = value;
        }
    });
    
    // Show loading
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Grading...';
    submitBtn.disabled = true;
    
    // Submit to server
    fetch('/submit-quiz', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            answers: answers,
            subject: form.dataset.subject
        })
    })
    .then(response => response.json())
    .then(data => {
        // Show results
        showQuizResults(data);
        
        // Update XP and level display
        updateUserStats(data.xp_earned, data.new_level);
        
        // Show medals if awarded
        if (data.medals_awarded && data.medals_awarded.length > 0) {
            showMedalAnimation(data.medals_awarded);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error submitting quiz. Please try again.');
    })
    .finally(() => {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    });
    
    return false;
}

function showQuizResults(data) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content animate-pop">
            <div class="modal-header">
                <h2>Quiz Results 🎉</h2>
                <button class="close-modal">&times;</button>
            </div>
            <div class="modal-body">
                <div class="result-score">
                    <div class="score-circle" data-score="${data.score}">
                        <span>${Math.round(data.score)}%</span>
                    </div>
                    <p>${data.correct} out of ${data.total} correct</p>
                </div>
                <div class="result-details">
                    <div class="detail-item">
                        <i class="fas fa-star"></i>
                        <span>XP Earned: +${data.xp_earned}</span>
                    </div>
                    ${data.medals_awarded && data.medals_awarded.length > 0 ? `
                    <div class="detail-item">
                        <i class="fas fa-medal"></i>
                        <span>Medals: ${data.medals_awarded.map(m => m.replace('_', ' ')).join(', ')}</span>
                    </div>
                    ` : ''}
                </div>
                <button class="btn btn-primary" onclick="this.closest('.modal').remove()">
                    Continue Learning
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Animate score circle
    setTimeout(() => {
        const circle = modal.querySelector('.score-circle');
        circle.style.setProperty('--score', data.score);
    }, 100);
    
    // Close modal
    modal.querySelector('.close-modal').addEventListener('click', () => modal.remove());
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.remove();
    });
}

function updateUserStats(xpEarned, newLevel) {
    const xpElement = document.querySelector('.xp-display');
    const levelElement = document.querySelector('.level-display');
    
    if (xpElement) {
        const currentXP = parseInt(xpElement.textContent) || 0;
        animateCounter(xpElement, currentXP, currentXP + xpEarned);
    }
    
    if (levelElement) {
        levelElement.textContent = newLevel;
        levelElement.classList.add('animate-bounce-in');
        setTimeout(() => levelElement.classList.remove('animate-bounce-in'), 1000);
    }
}

function showMedalAnimation(medals) {
    medals.forEach((medal, index) => {
        setTimeout(() => {
            const medalDiv = document.createElement('div');
            medalDiv.className = 'medal-earned-popup';
            medalDiv.innerHTML = `
                <div class="medal-icon" style="animation-delay: ${index * 200}ms">
                    <i class="fas fa-medal"></i>
                </div>
                <p>Earned: ${medal.replace('_', ' ')}</p>
            `;
            document.body.appendChild(medalDiv);
            
            setTimeout(() => medalDiv.remove(), 3000);
        }, index * 500);
    });
}

// Utility functions
function animateCounter(element, start, end, duration = 1000) {
    const range = end - start;
    const increment = range / (duration / 16); // 60fps
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
            current = end;
            clearInterval(timer);
        }
        element.textContent = Math.round(current);
    }, 16);
}

// Theme toggle (optional)
function toggleTheme() {
    const body = document.body;
    body.classList.toggle('dark-theme');
    
    // Save preference
    localStorage.setItem('theme', body.classList.contains('dark-theme') ? 'dark' : 'light');
}

// Load saved theme
if (localStorage.getItem('theme') === 'dark') {
    document.body.classList.add('dark-theme');
}

// Add CSS for modal and tooltips
const style = document.createElement('style');
style.textContent = `
    .modal {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 2000;
    }
    
    .modal-content {
        background: white;
        border-radius: 20px;
        padding: 2rem;
        max-width: 500px;
        width: 90%;
    }
    
    .modal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.5rem;
    }
    
    .close-modal {
        background: none;
        border: none;
        font-size: 2rem;
        cursor: pointer;
        color: var(--gray);
    }
    
    .score-circle {
        width: 150px;
        height: 150px;
        border-radius: 50%;
        background: conic-gradient(var(--primary) calc(var(--score) * 1%), var(--gray-light) 0);
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 1rem;
        position: relative;
    }
    
    .score-circle::before {
        content: '';
        position: absolute;
        width: 120px;
        height: 120px;
        background: white;
        border-radius: 50%;
    }
    
    .score-circle span {
        position: relative;
        z-index: 1;
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .medal-earned-popup {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        text-align: center;
        z-index: 3000;
    }
    
    .medal-icon {
        font-size: 4rem;
        color: gold;
        margin-bottom: 1rem;
        animation: medalPop 1s cubic-bezier(0.68, -0.55, 0.265, 1.55);
    }
    
    .tooltip {
        position: absolute;
        background: var(--dark);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-size: 0.875rem;
        z-index: 1000;
        pointer-events: none;
        white-space: nowrap;
    }
    
    .tooltip::after {
        content: '';
        position: absolute;
        top: 100%;
        left: 50%;
        transform: translateX(-50%);
        border-width: 5px;
        border-style: solid;
        border-color: var(--dark) transparent transparent transparent;
    }
    
    .dark-theme {
        background: #1a202c;
        color: #e2e8f0;
    }
    
    .dark-theme .card {
        background: #2d3748;
        color: #e2e8f0;
    }
`;
document.head.appendChild(style);