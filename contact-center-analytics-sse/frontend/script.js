document.addEventListener('DOMContentLoaded', () => {
    // --- API Configuration ---
    const API_BASE_URL = 'http://127.0.0.1:8000';

    // --- Global State ---
    let currentAnalysisResult = null;
    let currentAudioURL = null;
    let localSopData = null;
    let localQuestionnaireData = null;

    // --- DOM Element Selectors ---
    const nav = {
        home: document.getElementById('nav-home'),
        persona: document.getElementById('nav-persona'),
        sop: document.getElementById('nav-sop'),
        questionnaire: document.getElementById('nav-questionnaire'),
        ask: document.getElementById('nav-ask')
    };
    const pages = {
        home: document.getElementById('home-page'),
        persona: document.getElementById('persona-page'),
        sop: document.getElementById('sop-page'),
        questionnaire: document.getElementById('questionnaire-page'),
        ask: document.getElementById('ask-questions-page')
    };
    const uploadForm = document.getElementById('upload-form');
    const audioFileInput = document.getElementById('audio-file');
    const loader = document.getElementById('loader');
    const resultsContainer = document.getElementById('results-container');
    const audioPlayer = document.getElementById('audio-player');

    // SOP Edit Selectors
    const sopViewContainer = document.getElementById('sop-view-container');
    const sopEditContainer = document.getElementById('sop-edit-container');
    const editSopBtn = document.getElementById('edit-sop-btn');
    const saveSopBtn = document.getElementById('save-sop-btn');
    const cancelSopBtn = document.getElementById('cancel-sop-btn');
    const sopEditTextarea = document.getElementById('sop-edit-textarea');

    // Questionnaire Edit Selectors
    const questionnaireViewContainer = document.getElementById('questionnaire-view-container');
    const questionnaireEditContainer = document.getElementById('questionnaire-edit-container');
    const editQuestionnaireBtn = document.getElementById('edit-questionnaire-btn');
    const saveQuestionnaireBtn = document.getElementById('save-questionnaire-btn');
    const cancelQuestionnaireBtn = document.getElementById('cancel-questionnaire-btn');
    const questionnaireEditTextarea = document.getElementById('questionnaire-edit-textarea');

    // --- Page Navigation ---
    const showPage = (pageId) => {
        Object.values(pages).forEach(page => page.classList.add('d-none'));
        Object.values(nav).forEach(link => link.classList.remove('active'));
        pages[pageId].classList.remove('d-none');
        nav[pageId].classList.add('active');
    };

    nav.home.addEventListener('click', (e) => { e.preventDefault(); showPage('home'); });
    nav.persona.addEventListener('click', (e) => { e.preventDefault(); if (!nav.persona.classList.contains('disabled')) showPage('persona'); });
    nav.sop.addEventListener('click', (e) => { e.preventDefault(); showPage('sop'); if (!localSopData) loadSopData(); });
    nav.questionnaire.addEventListener('click', (e) => { e.preventDefault(); showPage('questionnaire'); if (!localQuestionnaireData) loadQuestionnaireData(); });
    nav.ask.addEventListener('click', (e) => {
        e.preventDefault();
        if (!nav.ask.classList.contains('disabled')) {
            showPage('ask');
            setupAskQuestionsPage();
        }
    });

    // --- Data Loading & Rendering for SOP/Questionnaire Pages ---
    async function loadSopData() {
        renderSopTable({ loading: true });
        try {
            const response = await fetch(`${API_BASE_URL}/api/sop`);
            if (!response.ok) throw new Error(`Network response was not ok: ${response.statusText}`);
            localSopData = await response.json();
            renderSopTable(localSopData);
        } catch (error) {
            console.error("Failed to load SOP data:", error);
            renderSopTable({ error: error.message });
        }
    }

    function renderSopTable(data) {
        if (data.loading) { sopViewContainer.innerHTML = `<p class="text-muted">Loading...</p>`; return; }
        if (data.error || !data.sop_checklist) { sopViewContainer.innerHTML = `<div class="alert alert-danger"><strong>Error:</strong> Could not load Script Adherence data.</div>`; return; }
        let tableHtml = `<div class="card shadow-sm"><div class="table-responsive"><table class="table table-hover mb-0"><thead class="table-light-custom-header"><tr><th>Key</th><th>Compliance Point</th></tr></thead><tbody>${data.sop_checklist.map(item => `<tr><td><span class="badge bg-secondary">${item.key || 'N/A'}</span></td><td>${item.point || 'N/A'}</td></tr>`).join('')}</tbody></table></div></div>`;
        sopViewContainer.innerHTML = tableHtml;
    }

    async function loadQuestionnaireData() {
        renderQuestionnaireTable({ loading: true });
        try {
            const response = await fetch(`${API_BASE_URL}/api/questionnaire`);
            if (!response.ok) throw new Error(`Network response was not ok: ${response.statusText}`);
            localQuestionnaireData = await response.json();
            renderQuestionnaireTable(localQuestionnaireData);
        } catch (error) {
            console.error("Failed to load questionnaire data:", error);
            renderQuestionnaireTable({ error: error.message });
        }
    }

    function renderQuestionnaireTable(data) {
        if (data.loading) { questionnaireViewContainer.innerHTML = `<p class="text-muted">Loading...</p>`; return; }
        if (data.error || !data.lead_scoring_questionnaire) { questionnaireViewContainer.innerHTML = `<div class="alert alert-danger"><strong>Error:</strong> Could not load Questionnaire data.</div>`; return; }
        let tableHtml = `<div class="card shadow-sm"><div class="table-responsive"><table class="table table-hover mb-0"><thead class="table-light-custom-header"><tr><th>Key</th><th>Question</th><th>Priority Answers</th></tr></thead><tbody>${data.lead_scoring_questionnaire.map(item => `<tr><td><span class="badge bg-secondary">${item.key || 'N/A'}</span></td><td>${item.question || 'N/A'}</td><td>${(item.priority_answers || []).map(ans => `<span class="badge bg-success me-1">${ans}</span>`).join(' ')}</td></tr>`).join('')}</tbody></table></div></div>`;
        questionnaireViewContainer.innerHTML = tableHtml;
    }

    // --- Edit/Save/Cancel Functionality ---
    const toggleEditView = (viewContainer, editContainer, data, textarea) => {
        viewContainer.classList.toggle('d-none');
        editContainer.classList.toggle('d-none');
        if (data && !editContainer.classList.contains('d-none')) {
            textarea.value = jsyaml.dump(data);
        }
    };

    editSopBtn.addEventListener('click', () => { if (localSopData) toggleEditView(sopViewContainer, sopEditContainer, localSopData, sopEditTextarea); });
    cancelSopBtn.addEventListener('click', () => toggleEditView(sopViewContainer, sopEditContainer, localSopData, sopEditTextarea));
    saveSopBtn.addEventListener('click', () => {
        try {
            localSopData = jsyaml.load(sopEditTextarea.value);
            renderSopTable(localSopData);
            toggleEditView(sopViewContainer, sopEditContainer, null, sopEditTextarea);
            alert('SOP updated locally for this session.');
        } catch (e) { alert(`Error parsing YAML: ${e.message}`); }
    });

    editQuestionnaireBtn.addEventListener('click', () => { if (localQuestionnaireData) toggleEditView(questionnaireViewContainer, questionnaireEditContainer, localQuestionnaireData, questionnaireEditTextarea); });
    cancelQuestionnaireBtn.addEventListener('click', () => toggleEditView(questionnaireViewContainer, questionnaireEditContainer, localQuestionnaireData, questionnaireEditTextarea));
    saveQuestionnaireBtn.addEventListener('click', () => {
        try {
            localQuestionnaireData = jsyaml.load(questionnaireEditTextarea.value);
            renderQuestionnaireTable(localQuestionnaireData);
            toggleEditView(questionnaireViewContainer, questionnaireEditContainer, null, questionnaireEditTextarea);
            alert('Questionnaire updated locally for this session.');
        } catch (e) { alert(`Error parsing YAML: ${e.message}`); }
    });

    // --- Home Page Logic ---
    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const audioFile = audioFileInput.files[0];
        if (!audioFile) { alert('Please select an audio file.'); return; }

        if (currentAudioURL) { URL.revokeObjectURL(currentAudioURL); }
        currentAudioURL = URL.createObjectURL(audioFile);
        audioPlayer.src = currentAudioURL;

        loader.classList.remove('d-none');
        resultsContainer.classList.add('d-none');
        audioPlayer.classList.add('d-none');
        nav.ask.classList.add('disabled');
        nav.persona.classList.add('disabled');
        currentAnalysisResult = null;

        const formData = new FormData();
        formData.append('audio', audioFile);

        try {
            const response = await fetch(`${API_BASE_URL}/api/process-audio`, { method: 'POST', body: formData });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'An unknown error occurred during analysis.');
            }
            const results = await response.json();
            displayResults(results);
        } catch (error) {
            console.error('Processing error:', error);
            alert(`Analysis Error: ${error.message}`);
        } finally {
            loader.classList.add('d-none');
        }
    });

    // --- Result Rendering Functions ---
    function displayResults(data) {
        if (!data) { alert("Received empty analysis results from the server."); return; }
        currentAnalysisResult = data;
        nav.ask.classList.remove('disabled');
        nav.persona.classList.remove('disabled');

        renderLeadScore(data.call_quality_summary, data.lead_scoring_report);
        renderPersonaSummary(data.customer_persona?.persona_summary);
        renderDetailedPersona(data.customer_persona);
        renderCallQualityCallouts(data.call_quality_summary);
        renderSopAdherence(data.sop_adherence_report);
        renderTranscript(data.transcript, 'home-transcript-details');

        audioPlayer.classList.remove('d-none');
        resultsContainer.classList.remove('d-none');
    }

    function renderLeadScore(summary, report) {
        const container = document.getElementById('lead-score-card');
        if (!summary || summary.lead_hotness_score === undefined) {
            container.innerHTML = `<p class="text-muted">No score available</p>`;
            return;
        }
        const score = parseInt(summary.lead_hotness_score);
        let colorClass = 'bg-lead-cold';
        if (score >= 75) colorClass = 'bg-lead-hot';
        else if (score >= 40) colorClass = 'bg-lead-warm';

        let justificationHtml = '<div class="justification-grid">';
        if (report && Array.isArray(report)) {
            report.forEach(item => {
                const status = {
                    icon: item.answered ? '✔' : '–',
                    className: item.answered ? 'yes' : 'na'
                };
                const label = item.question.split('(')[0].replace('What is the customer\'s', '').replace('Does the customer', '').trim();
                justificationHtml += `
                    <div class="justification-item-simple">
                        <span class="justification-label-simple">${label}</span>
                        <span class="justification-icon ${status.className}">${status.icon}</span>
                    </div>`;
            });
        }
        justificationHtml += '</div>';

        const overviewHtml = `
            <div class="lead-overview">
                <p><strong>Call Quality:</strong> ${summary.overall_call_quality || 'N/A'}</p>
                <p><strong>Lead Status:</strong> ${summary.overall_lead_quality || 'N/A'}</p>
                <p><strong>Next Step:</strong> ${summary.required_follow_up || 'Not specified'}</p>
            </div>
        `;

        container.innerHTML = `
            <div class="lead-score-card-content">
                <div class="lead-score-display ${colorClass}">${score}%</div>
                <p class="mt-2 mb-0 text-muted-custom">Likelihood to Convert</p>
                ${justificationHtml}
                ${overviewHtml}
            </div>
        `;
    }

    function renderPersonaSummary(summary) {
        const container = document.getElementById('persona-summary-card');
        if (!summary) { container.innerHTML = `<p class="text-muted">No summary available</p>`; return; }

        const getTraitIcon = (trait) => {
            const lowerTrait = trait.toLowerCase();
            if (lowerTrait.includes('cost') || lowerTrait.includes('price') || lowerTrait.includes('budget')) return '💰';
            if (lowerTrait.includes('quality') || lowerTrait.includes('reliable')) return '🛡️';
            if (lowerTrait.includes('urgency') || lowerTrait.includes('immediate')) return '⏰';
            if (lowerTrait.includes('sustainability') || lowerTrait.includes('green')) return '🌱';
            if (lowerTrait.includes('concern') || lowerTrait.includes('barrier')) return '❓';
            return '🔹';
        };

        const getPotentialStyling = (score) => {
            const lowerScore = (score || '').toLowerCase();
            switch (lowerScore) {
                case 'high': return { width: '95%', label: 'High' };
                case 'medium': return { width: '60%', label: 'Medium' };
                case 'low': return { width: '25%', label: 'Low' };
                default: return { width: '0%', label: 'N/A' };
            }
        };
        const potential = getPotentialStyling(summary.lead_potential_score);

        container.innerHTML = `
            <p class="persona-tagline">"${summary.persona_tagline || 'Tagline not available'}"</p>
            <div>
                ${(summary.three_key_traits || []).map(trait => `
                    <div class="persona-trait-card">
                        <span class="trait-icon">${getTraitIcon(trait)}</span>
                        <span class="trait-text">${trait}</span>
                    </div>`).join('')}
            </div>
            <div class="potential-bar-container">
                <h6>Lead Potential</h6>
                <div class="progress">
                    <div class="progress-bar progress-bar-gradient" role="progressbar" style="width: ${potential.width};" aria-valuenow="${potential.width}" aria-valuemin="0" aria-valuax="100">
                        ${potential.label}
                    </div>
                </div>
            </div>`;
    }

    function renderDetailedPersona(personaData) {
        const container = document.getElementById('detailed-persona-container');
        if (!personaData || !personaData.detailed_analysis) {
            container.innerHTML = `<div class="alert alert-warning">Detailed persona analysis is not available for this call.</div>`; return;
        }
        let html = '<div class="row g-4">';
        personaData.detailed_analysis.forEach(category => {
            html += `<div class="col-md-6"><div class="card h-100 shadow-sm"><div class="card-header bg-gradient-header">${category.category}</div><div class="card-body"><dl class="mb-0">${category.points.map(point => `<dt class="text-primary-gradient">${point.label}</dt><dd class="mb-3"><strong>Value:</strong> ${point.value || 'N/A'}<br><small class="text-muted-custom"><strong>Citation:</strong> <em>${point.citation || 'None'}</em><br><strong>Commentary:</strong> <em>${point.commentary || 'None'}</em></small></dd>`).join('')}</dl></div></div></div>`;
        });
        html += '</div>';
        container.innerHTML = html;
    }

    function renderCallQualityCallouts(summary) {
        const container = document.getElementById('call-quality-callouts');
        if (!summary) { container.innerHTML = ''; return; }
        const checkIcon = (value) => value ? `<span class="callout-check-icon text-success">✔</span>` : `<span class="callout-check-icon text-danger">✖</span>`;
        container.innerHTML = `<div class="col-md-3"><div class="callout-card"><h6>Overall Call Quality</h6><p>${summary.overall_call_quality || 'N/A'}</p></div></div><div class="col-md-3"><div class="callout-card"><h6>Overall Lead Quality</h6><p>${summary.overall_lead_quality || 'N/A'}</p></div></div><div class="col-md-6"><div class="callout-card"><h6>Required Follow-up</h6><p>${summary.required_follow_up || 'None specified'}</p></div></div><div class="col-md-3"><div class="callout-card"><h6>Greetings Check</h6><p>Performed ${checkIcon(summary.greetings_check)}</p></div></div><div class="col-md-3"><div class="callout-card"><h6>Rapport Building</h6><p>Attempted ${checkIcon(summary.rapport_building_check)}</p></div></div><div class="col-md-3"><div class="callout-card"><h6>Needs Analysis</h6><p>Performed ${checkIcon(summary.needs_analysis_check)}</p></div></div><div class="col-md-3"><div class="callout-card"><h6>Product Recommendation</h6><p>Performed ${checkIcon(summary.product_recommendation_check)}</p></div></div>`;
    }

    function renderSopAdherence(report) {
        const container = document.getElementById('sop-adherence-details');
        if (!report || !Array.isArray(report) || report.length === 0) { container.innerHTML = `<p class="text-muted">No Script Adherence report available.</p>`; return; }
        const compliedCount = report.filter(item => item.compliance === "Fully Covered" || item.compliance === "Partially Covered").length;
        const totalCount = report.length;
        const percentage = totalCount > 0 ? Math.round((compliedCount / totalCount) * 100) : 0;
        const getStatusIcon = (compliance) => {
            if (compliance === "Fully Covered") return '✅'; if (compliance === "Partially Covered") return '⚠️'; if (compliance === "Not Covered") return '❌'; return '❓';
        };
        container.innerHTML = `<h5 class="mb-3">Overall Score: <span class="text-success-custom">${compliedCount}</span>/<span class="text-primary-main-text">${totalCount}</span> (<span class="text-warning-custom">${percentage}%</span>)</h5><div class="table-responsive"><table class="table table-sm"><thead><tr><th class="text-primary-gradient">Status</th><th class="text-primary-gradient">Script Point</th><th class="text-primary-gradient">Commentary</th><th class="text-primary-gradient">Evidence</th></tr></thead><tbody>${report.map(item => `<tr><td class="text-center">${getStatusIcon(item.compliance)}</td><td>${item.sop_point}</td><td><em class="text-muted-custom small">${item.commentary || 'N/A'}</em></td><td><em class="text-muted-custom small">${item.evidence || 'Not found'}</em></td></tr>`).join('')}</tbody></table></div>`;
    }

    function renderTranscript(transcript, containerId) {
        const container = document.getElementById(containerId);
        if (!transcript || transcript.length === 0) { container.innerHTML = `<p class="text-muted">Transcript not available</p>`; return; }
        container.innerHTML = transcript.map(line => `<div class="transcript-line"><span class="${line.speaker?.toLowerCase().includes('agent') ? 'speaker-agent' : 'speaker-customer'}">${line.speaker || 'Unknown'}:</span> <span>${line.transcript_english}</span></div>`).join('');
    }

    // --- "Ask Specific Questions" Page Logic ---
    function setupAskQuestionsPage() {
        const container = document.getElementById('ask-page-content');
        if (!currentAnalysisResult) {
            container.innerHTML = `<div class="alert alert-warning">Please process a call on the Home page first to enable this feature.</div>`; return;
        }
        container.innerHTML = `<div id="chat-container"></div><form id="ask-question-form" class="mt-3"><div class="input-group"><input type="text" class="form-control" id="question-input" placeholder="Ask a question about the call..." required><button type="submit" class="btn btn-primary-gradient">Send</button></div></form><div class="accordion mt-4" id="transcriptAccordion"><div class="accordion-item"><h2 class="accordion-header" id="headingOne"><button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseOne" aria-expanded="false" aria-controls="collapseOne">View Full Call Transcripts</button></h2><div id="collapseOne" class="accordion-collapse collapse" aria-labelledby="headingOne" data-bs-parent="#transcriptAccordion"><div class="accordion-body"><div class="transcript-grid"><div class="transcript-column card shadow-sm"><div class="card-header bg-gradient-header">Original Language</div><div class="card-body transcript-box" id="transcript-original-col"></div></div><div class="transcript-column card shadow-sm"><div class="card-header bg-gradient-header">English Translation</div><div class="card-body transcript-box" id="transcript-english-col"></div></div></div></div></div></div></div>`;
        renderDualTranscript(currentAnalysisResult.transcript);
        document.getElementById('ask-question-form').addEventListener('submit', handleQuestionSubmit);
    }

    function renderDualTranscript(transcript) {
        const originalCol = document.getElementById('transcript-original-col');
        const englishCol = document.getElementById('transcript-english-col');
        if (!originalCol || !englishCol) return;
        const render = (segment, key) => `<div class="transcript-line"><span class="${segment.speaker?.toLowerCase().includes('agent') ? 'speaker-agent' : 'speaker-customer'}">${segment.speaker || 'Unknown'}:</span> <span>${segment[key] || '(Not available)'}</span></div>`;
        originalCol.innerHTML = transcript.map(line => render(line, 'transcript_local_language')).join('');
        englishCol.innerHTML = transcript.map(line => render(line, 'transcript_english')).join('');
    }

    async function handleQuestionSubmit(e) {
        e.preventDefault();
        const questionInput = document.getElementById('question-input');
        const chatContainer = document.getElementById('chat-container');
        const question = questionInput.value.trim();
        if (!question) return;

        const userBubble = document.createElement('div');
        userBubble.className = 'chat-bubble user-question';
        userBubble.textContent = question;
        chatContainer.appendChild(userBubble);
        questionInput.value = '';
        chatContainer.scrollTop = chatContainer.scrollHeight;

        const thinkingBubble = document.createElement('div');
        thinkingBubble.className = 'chat-bubble ai-answer';
        thinkingBubble.innerHTML = `<span class="ai-answer-prefix">DialogIQ AI:</span><div class="spinner-border spinner-border-sm" role="status"></div>`;
        chatContainer.appendChild(thinkingBubble);
        chatContainer.scrollTop = chatContainer.scrollHeight;

        const englishTranscriptText = currentAnalysisResult.transcript.map(line => `${line.speaker}: ${line.transcript_english}`).join('\n');

        try {
            const response = await fetch(`${API_BASE_URL}/api/ask-question`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ transcript_text: englishTranscriptText, question: question })
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to get an answer.');
            }
            const data = await response.json();
            const formattedAnswer = data.answer.replace(/\n/g, '<br>');
            thinkingBubble.innerHTML = `<span class="ai-answer-prefix">DialogIQ AI:</span>${formattedAnswer}`;
        } catch (error) {
            thinkingBubble.innerHTML = `<span class="ai-answer-prefix">DialogIQ AI:</span><span class="text-danger">Error: ${error.message}</span>`;
        } finally {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    }
});