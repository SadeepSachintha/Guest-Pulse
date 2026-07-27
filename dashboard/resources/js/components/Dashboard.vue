<template>
  <div class="app-layout">
    <!-- Sidebar -->
    <aside class="app-sidebar">
      <div class="brand">
        <i class="fa-solid fa-heart-pulse brand-icon"></i>
        <span class="brand-text">Guest Pulse</span>
      </div>
      
      <ul class="nav-menu">
        <li class="nav-item active">
          <a href="#">
            <i class="fa-solid fa-chart-line"></i>
            Dashboard
          </a>
        </li>
        <li class="nav-item" :class="{ active: isIntegrationsDrawerOpen }">
          <a href="#" @click.prevent="isIntegrationsDrawerOpen = true">
            <i class="fa-solid fa-sliders"></i>
            Integrations
          </a>
        </li>
        <li class="nav-item" :class="{ active: isHelpDrawerOpen }">
          <a href="#" @click.prevent="isHelpDrawerOpen = true">
            <i class="fa-solid fa-circle-question"></i>
            Help Support
          </a>
        </li>
      </ul>
      
      <div class="sidebar-footer">
        <div class="avatar">GP</div>
        <div class="user-info">
          <span class="user-name">Manager Hub</span>
          <span class="user-role">Administrator</span>
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="app-main">
      <!-- Header -->
      <header class="dashboard-header">
        <div class="header-title">
          <h1>Reputation Insights</h1>
          <p>Monitor reviews, NLP sentiments, and draft AI response suggestions.</p>
        </div>
        <div>
          <button 
            @click="fetchNewReviews" 
            class="btn-primary" 
            :disabled="fetchingNew"
          >
            <i v-if="fetchingNew" class="fa-solid fa-spinner spinner"></i>
            <i v-else class="fa-solid fa-arrows-rotate"></i>
            {{ fetchingNew ? 'Ingesting Reviews...' : 'Fetch New Reviews' }}
          </button>
        </div>
      </header>

      <!-- KPI Grid -->
      <section class="stats-grid">
        <!-- Card 1 -->
        <div class="stat-card">
          <div class="stat-icon reviews">
            <i class="fa-solid fa-comments"></i>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ kpis.total_reviews }}</span>
            <span class="stat-label">Total Reviews</span>
          </div>
        </div>
        <!-- Card 2 -->
        <div class="stat-card">
          <div class="stat-icon rating">
            <i class="fa-solid fa-star"></i>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ kpis.avg_rating }} / 5</span>
            <span class="stat-label">Average Rating</span>
          </div>
        </div>
        <!-- Card 3 -->
        <div class="stat-card">
          <div class="stat-icon sentiment">
            <i class="fa-solid fa-face-smile"></i>
          </div>
          <div class="stat-info">
            <span class="stat-value" :class="getSentimentClass(kpis.avg_sentiment)">
              {{ kpis.avg_sentiment > 0 ? '+' : '' }}{{ kpis.avg_sentiment }}
            </span>
            <span class="stat-label">Sentiment Index</span>
          </div>
        </div>
        <!-- Card 4 -->
        <div class="stat-card">
          <div class="stat-icon replies">
            <i class="fa-solid fa-reply-all"></i>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ kpis.response_rate }}%</span>
            <span class="stat-label">Reply Rate</span>
          </div>
        </div>
      </section>

      <!-- Charts Grid -->
      <section class="charts-grid" v-show="kpis.total_reviews > 0">
        <!-- Sentiment Line Chart -->
        <div class="chart-card">
          <div class="chart-card-header">
            <h3>Sentiment Score Over Time</h3>
            <span class="review-date">Compound score (-1.0 to 1.0)</span>
          </div>
          <div class="chart-container">
            <canvas ref="sentimentChartCanvas"></canvas>
          </div>
        </div>

        <!-- Review Sources / Aspect Breakdown -->
        <div class="chart-card">
          <div class="chart-card-header">
            <h3>Review Sources</h3>
          </div>
          <div class="chart-container" style="height: 220px;">
            <canvas ref="sourceChartCanvas"></canvas>
          </div>
        </div>
      </section>

      <!-- Aspects Breakdown Card -->
      <section class="chart-card mb-2" style="margin-bottom: 2.5rem;" v-show="kpis.total_reviews > 0">
        <div class="chart-card-header">
          <h3>Aspect-Based Sentiment Mining (NLP)</h3>
          <p style="font-size: 0.85rem; color: var(--text-muted)">Identifies specific guest talking points and calculates local sentiments</p>
        </div>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 2rem; margin-top: 1rem;">
          <div v-for="(counts, aspect) in stats.aspects" :key="aspect" class="aspect-bar-item">
            <div class="aspect-bar-header">
              <span class="aspect-bar-title">{{ aspect === 'wifi' ? 'Wi-Fi' : aspect }}</span>
              <span class="aspect-bar-values">
                <span style="color: var(--success)">{{ counts.positive }}</span> / 
                <span style="color: var(--danger)">{{ counts.negative }}</span> / 
                <span style="color: var(--text-muted)">{{ counts.neutral }}</span>
              </span>
            </div>
            <div class="aspect-bar-track">
              <div 
                class="aspect-bar-fill positive" 
                :style="{ width: getAspectPercentage(counts.positive, counts) + '%' }" 
                title="Positive"
              ></div>
              <div 
                class="aspect-bar-fill neutral" 
                :style="{ width: getAspectPercentage(counts.neutral, counts) + '%' }" 
                title="Neutral"
              ></div>
              <div 
                class="aspect-bar-fill negative" 
                :style="{ width: getAspectPercentage(counts.negative, counts) + '%' }" 
                title="Negative"
              ></div>
            </div>
          </div>
        </div>
      </section>

      <!-- Escalation Banner -->
      <div v-if="escalatedReviews.length > 0" style="background: rgba(244, 63, 94, 0.06); border: 1px solid rgba(244, 63, 94, 0.2); padding: 1.25rem; border-radius: 16px; margin-bottom: 2rem; display: flex; flex-direction: column; gap: 0.75rem;">
        <div style="display: flex; align-items: center; justify-content: space-between;">
          <h4 style="color: var(--danger); display: flex; align-items: center; gap: 0.5rem; font-size: 1rem; font-weight: 700;">
            <i class="fa-solid fa-triangle-exclamation"></i>
            Critical Escalation: {{ escalatedReviews.length }} Review(s) Require GM Attention
          </h4>
          <span style="font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.5px; background: var(--danger); color: white; padding: 0.25rem 0.6rem; border-radius: 4px; font-weight: 700;">Action Required</span>
        </div>
        <p style="font-size: 0.85rem; color: var(--text-muted); line-height: 1.4;">
          These guest reviews scored very low on NLP sentiment checks and require immediate service recovery response.
        </p>
        <div style="display: flex; flex-direction: column; gap: 0.5rem; margin-top: 0.25rem;">
          <div v-for="rev in escalatedReviews" :key="rev.id" style="background: rgba(0,0,0,0.15); padding: 0.75rem 1rem; border-radius: 10px; display: flex; justify-content: space-between; align-items: center; border-left: 3px solid var(--danger);">
            <div style="font-size: 0.85rem; display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
              <span class="source-badge" :class="rev.source" style="padding: 0.2rem 0.4rem; font-size: 0.65rem;">{{ rev.source }}</span>
              <strong>{{ rev.reviewer_name }}</strong>: <span style="color: var(--text-main);">"{{ truncateText(rev.review_text, 70) }}"</span>
            </div>
            <button @click="openResponseDrawer(rev)" class="btn-primary btn-sm" style="padding: 0.35rem 0.75rem; font-size: 0.75rem; background: var(--danger); box-shadow: none; flex-shrink: 0;">
              Resolve Now
            </button>
          </div>
        </div>
      </div>

      <!-- Reviews Feed -->
      <section class="feed-section">
        <div class="feed-header">
          <h3>Online Guest Reviews</h3>
          
          <div class="filters-bar">
            <!-- Search -->
            <div class="search-wrapper">
              <i class="fa-solid fa-magnifying-glass"></i>
              <input 
                type="text" 
                v-model="filters.search" 
                @input="debounceSearch" 
                placeholder="Search reviews..." 
                class="search-input"
              >
            </div>
            
            <!-- Source Filter -->
            <select v-model="filters.source" @change="fetchReviews" class="select-filter">
              <option value="">All Sources</option>
              <option value="google">Google</option>
              <option value="booking">Booking.com</option>
              <option value="tripadvisor">TripAdvisor</option>
            </select>
            
            <!-- Sentiment Filter -->
            <select v-model="filters.sentiment" @change="fetchReviews" class="select-filter">
              <option value="">All Sentiments</option>
              <option value="positive">Positive</option>
              <option value="neutral">Neutral</option>
              <option value="negative">Negative</option>
            </select>
            
            <!-- Rating Filter -->
            <select v-model="filters.rating" @change="fetchReviews" class="select-filter">
              <option value="">All Ratings</option>
              <option value="5">5 Stars</option>
              <option value="4">4 Stars</option>
              <option value="3">3 Stars</option>
              <option value="2">2 Stars</option>
              <option value="1">1 Star</option>
            </select>
          </div>
        </div>

        <!-- Loader -->
        <div v-if="loadingReviews" class="empty-state">
          <i class="fa-solid fa-spinner spinner"></i>
          <p>Loading guest reviews...</p>
        </div>

        <!-- Empty State -->
        <div v-else-if="reviews.length === 0" class="empty-state">
          <i class="fa-solid fa-comments-slash"></i>
          <p>No reviews found matching the filters.</p>
          <button @click="fetchNewReviews" class="btn-secondary btn-sm" style="margin-top: 0.5rem">
            Fetch Initial Mock Reviews
          </button>
        </div>

        <!-- Feed List -->
        <div v-else class="reviews-list">
          <div 
            v-for="review in reviews" 
            :key="review.id" 
            class="review-item"
          >
            <div class="review-top">
              <div class="reviewer-meta">
                <span class="source-badge" :class="review.source">
                  <i :class="getSourceIcon(review.source)"></i>
                  {{ review.source === 'google' ? 'Google' : (review.source === 'booking' ? 'Booking.com' : 'TripAdvisor') }}
                </span>
                <span class="reviewer-name">{{ review.reviewer_name }}</span>
                <div class="review-stars">
                  <i 
                    v-for="star in 5" 
                    :key="star" 
                    class="fa-star" 
                    :class="star <= review.rating ? 'fa-solid' : 'fa-regular'"
                  ></i>
                </div>
              </div>
              <div class="review-right">
                <span class="review-date">{{ formatDate(review.review_date) }}</span>
                <span class="sentiment-badge" :class="review.sentiment_label">
                  Sentiment: {{ review.sentiment_label }} ({{ review.sentiment_score > 0 ? '+' : '' }}{{ review.sentiment_score }})
                </span>
              </div>
            </div>

            <p class="review-content" v-html="highlightReviewText(review)"></p>

            <!-- Aspects Found -->
            <div class="aspect-tags" v-if="review.aspect_sentiments && Object.keys(review.aspect_sentiments).length > 0">
              <span 
                v-for="(sentiment, aspect) in review.aspect_sentiments" 
                :key="aspect" 
                class="aspect-tag" 
                :class="sentiment"
              >
                <i :class="sentiment === 'positive' ? 'fa-solid fa-circle-plus' : (sentiment === 'negative' ? 'fa-solid fa-circle-minus' : 'fa-solid fa-circle-info')"></i>
                {{ aspect === 'wifi' ? 'Wi-Fi' : aspect }}: {{ sentiment }}
              </span>
            </div>

            <!-- Footer Actions -->
            <div class="review-actions">
              <div class="action-status">
                <span class="status-indicator" :class="review.response_status"></span>
                <span>Response status: <strong>{{ review.response_status }}</strong></span>
              </div>
              
              <div class="action-buttons">
                <button 
                  v-if="review.response_status === 'pending'"
                  @click="ignoreReview(review)" 
                  class="btn-secondary btn-sm"
                >
                  Ignore
                </button>
                <button 
                  @click="openResponseDrawer(review)" 
                  class="btn-primary btn-sm"
                >
                  <i class="fa-solid fa-robot"></i>
                  {{ review.response_status === 'replied' ? 'View/Edit Reply' : 'Generate AI Reply' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>

    <!-- Side Response Drawer -->
    <div 
      v-if="isDrawerOpen" 
      class="side-drawer-backdrop" 
      @click="closeDrawer"
    ></div>
    
    <div class="side-drawer" :class="{ open: isDrawerOpen }">
      <div class="drawer-header">
        <h3>AI Reply Suggestions</h3>
        <button @click="closeDrawer" class="btn-close">
          <i class="fa-solid fa-xmark"></i>
        </button>
      </div>

      <div class="drawer-body" v-if="selectedReview">
        <!-- Review Context -->
        <div class="review-preview">
          <div class="preview-meta">
            <span>By {{ selectedReview.reviewer_name }}</span>
            <span>Rating: {{ selectedReview.rating }} / 5</span>
          </div>
          <p class="preview-text">"{{ selectedReview.review_text }}"</p>
        </div>

        <!-- Tone Selector -->
        <div class="tone-selector" v-if="selectedReview.response_status !== 'replied' && !generatingResponse" style="margin-top: 0.5rem; display: flex; flex-direction: column; gap: 0.4rem;">
          <label for="response-tone" style="font-size: 0.9rem; font-weight: 600;">Response Tone:</label>
          <select 
            id="response-tone" 
            v-model="selectedTone" 
            @change="regenerateSuggestedResponse" 
            class="select-filter" 
            style="width: 100%; min-width: unset; background: rgba(255,255,255,0.03);"
          >
            <option value="professional">💼 Professional (Default)</option>
            <option value="casual">👋 Casual & Friendly</option>
            <option value="apologetic">🤝 Apologetic & Remedial</option>
            <option value="thankful">💖 Enthusiastic & Thankful</option>
          </select>
        </div>

        <!-- Loading suggestion -->
        <div v-if="generatingResponse" class="empty-state" style="padding: 2rem">
          <i class="fa-solid fa-spinner spinner" style="font-size: 2rem"></i>
          <p>Drafting context-aware response using local NLP...</p>
        </div>

        <!-- Suggestion Editor -->
        <div v-else class="response-composer">
          <label for="response-draft">Review & Edit AI Response Draft:</label>
          <textarea 
            id="response-draft" 
            v-model="responseDraft" 
            class="response-textarea" 
            placeholder="Edit the reply suggestion here..."
          ></textarea>
        </div>
      </div>

      <div class="drawer-footer" v-if="!generatingResponse && selectedReview">
        <button @click="closeDrawer" class="btn-secondary">Cancel</button>
        <button 
          @click="submitReply" 
          class="btn-primary" 
          :disabled="savingReply || !responseDraft.trim()"
        >
          <i v-if="savingReply" class="fa-solid fa-spinner spinner"></i>
          Save & Mark Replied
        </button>
      </div>
    </div>

    <!-- Help Support Drawer -->
    <div 
      v-if="isHelpDrawerOpen" 
      class="side-drawer-backdrop" 
      @click="isHelpDrawerOpen = false"
    ></div>
    
    <div class="side-drawer" :class="{ open: isHelpDrawerOpen }">
      <div class="drawer-header">
        <h3>Help & Documentation</h3>
        <button @click="isHelpDrawerOpen = false" class="btn-close">
          <i class="fa-solid fa-xmark"></i>
        </button>
      </div>

      <div class="drawer-body" style="gap: 1.5rem;">
        <div style="background: rgba(99, 102, 241, 0.05); padding: 1.25rem; border-radius: 12px; border: 1px solid var(--primary-glow);">
          <h4 style="margin-bottom: 0.5rem; color: var(--primary);"><i class="fa-solid fa-circle-info"></i> Guest Pulse NLP FAQ</h4>
          <p style="font-size: 0.85rem; line-height: 1.4; color: var(--text-muted);">
            Welcome to the local help guide. Guest Pulse runs offline-first NLP processing pipelines linked directly to HMS 2.0.
          </p>
        </div>

        <div style="display: flex; flex-direction: column; gap: 1rem;">
          <details style="background: rgba(255,255,255,0.02); padding: 1rem; border-radius: 10px; border: 1px solid var(--card-border); cursor: pointer;" open>
            <summary style="font-weight: 600; font-size: 0.9rem; margin-bottom: 0.5rem; outline: none; list-style: none; display: flex; justify-content: space-between; align-items: center;">
              <span>📈 How is the Sentiment Index calculated?</span>
              <i class="fa-solid fa-chevron-down" style="font-size: 0.8rem; color: var(--text-muted);"></i>
            </summary>
            <p style="font-size: 0.85rem; line-height: 1.5; color: var(--text-muted); cursor: default;">
              We use the NLTK VADER lexicon algorithm to run sentiment polarity checks on the text. The compound sentiment score ranges from <strong>-1.0 (extremely negative)</strong> to <strong>+1.0 (extremely positive)</strong>. Index values above +0.15 are positive, and below -0.15 are negative.
            </p>
          </details>

          <details style="background: rgba(255,255,255,0.02); padding: 1rem; border-radius: 10px; border: 1px solid var(--card-border); cursor: pointer;">
            <summary style="font-weight: 600; font-size: 0.9rem; margin-bottom: 0.5rem; outline: none; list-style: none; display: flex; justify-content: space-between; align-items: center;">
              <span>🔍 What is Aspect-Based Sentiment Mining?</span>
              <i class="fa-solid fa-chevron-down" style="font-size: 0.8rem; color: var(--text-muted);"></i>
            </summary>
            <p style="font-size: 0.85rem; line-height: 1.5; color: var(--text-muted); cursor: default;">
              Instead of reading reviews only as a whole, our Python pipeline parses sentences to look for aspect keywords. For example, sentences containing <em>"wifi"</em> or <em>"internet"</em> are evaluated independently to isolate complaints about connection speeds from praises about food or location.
            </p>
          </details>

          <details style="background: rgba(255,255,255,0.02); padding: 1rem; border-radius: 10px; border: 1px solid var(--card-border); cursor: pointer;">
            <summary style="font-weight: 600; font-size: 0.9rem; margin-bottom: 0.5rem; outline: none; list-style: none; display: flex; justify-content: space-between; align-items: center;">
              <span>🤖 How do the AI reply suggestions work?</span>
              <i class="fa-solid fa-chevron-down" style="font-size: 0.8rem; color: var(--text-muted);"></i>
            </summary>
            <p style="font-size: 0.85rem; line-height: 1.5; color: var(--text-muted); cursor: default;">
              The AI Response Suggester is a localized, rules-based engine that maps sentiments (positive, neutral, negative) and targeted aspects into customized professional templates. It supports 4 distinct tones: Professional, Casual, Apologetic, and Thankful.
            </p>
          </details>

          <details style="background: rgba(255,255,255,0.02); padding: 1rem; border-radius: 10px; border: 1px solid var(--card-border); cursor: pointer;">
            <summary style="font-weight: 600; font-size: 0.9rem; margin-bottom: 0.5rem; outline: none; list-style: none; display: flex; justify-content: space-between; align-items: center;">
              <span>⚠️ What should I do if the NLP service goes offline?</span>
              <i class="fa-solid fa-chevron-down" style="font-size: 0.8rem; color: var(--text-muted);"></i>
            </summary>
            <p style="font-size: 0.85rem; line-height: 1.5; color: var(--text-muted); cursor: default;">
              If the Python server is offline, Laravel falls back to an offline rating-based analyzer. To restore NLP mining and custom response tone features, start the Python process from the terminal: <code>.venv\Scripts\python main.py</code> inside the <code>nlp-service</code> folder.
            </p>
          </details>
        </div>
      </div>
      
      <div class="drawer-footer">
        <button @click="isHelpDrawerOpen = false" class="btn-primary">Got it</button>
      </div>
    </div>

    <!-- Integrations & Settings Drawer -->
    <div 
      v-if="isIntegrationsDrawerOpen" 
      class="side-drawer-backdrop" 
      @click="isIntegrationsDrawerOpen = false"
    ></div>
    
    <div class="side-drawer" :class="{ open: isIntegrationsDrawerOpen }">
      <div class="drawer-header">
        <h3>Integrations & Feeds</h3>
        <button @click="isIntegrationsDrawerOpen = false" class="btn-close">
          <i class="fa-solid fa-xmark"></i>
        </button>
      </div>

      <div class="drawer-body" style="gap: 1.5rem;">
        <div style="background: rgba(16, 185, 129, 0.05); padding: 1.25rem; border-radius: 12px; border: 1px solid rgba(16, 185, 129, 0.2);">
          <h4 style="margin-bottom: 0.5rem; color: var(--success);"><i class="fa-solid fa-link"></i> HMS 2.0 Core Connected</h4>
          <p style="font-size: 0.85rem; line-height: 1.4; color: var(--text-muted);">
            Linked directly to your HMS SQLite database. Reputation scores and replied status sync globally with guest files.
          </p>
        </div>

        <p style="font-size: 0.9rem; font-weight: 600; margin-bottom: -0.5rem;">Active Scraping Channels</p>
        <div style="display: flex; flex-direction: column; gap: 1rem;">
          <!-- Google Toggles -->
          <div style="background: rgba(255,255,255,0.02); padding: 1.25rem; border-radius: 12px; border: 1px solid var(--card-border); display: flex; justify-content: space-between; align-items: center;">
            <div style="display: flex; align-items: center; gap: 1rem;">
              <span class="source-badge google"><i class="fa-brands fa-google"></i></span>
              <div style="display: flex; flex-direction: column;">
                <span style="font-weight: 600; font-size: 0.9rem;">Google Business</span>
                <span style="font-size: 0.75rem; color: var(--text-muted);">Simulated Google Maps Reviews</span>
              </div>
            </div>
            <label class="switch-toggle" style="position: relative; display: inline-block; width: 44px; height: 24px;">
              <input type="checkbox" v-model="integrations.google" style="opacity: 0; width: 0; height: 0;">
              <span class="slider-toggle" :style="{ 
                position: 'absolute', cursor: 'pointer', top: 0, left: 0, right: 0, bottom: 0, 
                backgroundColor: integrations.google ? 'var(--success)' : 'rgba(255,255,255,0.1)', 
                borderRadius: '24px', transition: '0.3s' 
              }">
                <span :style="{ 
                  position: 'absolute', content: '', height: '18px', width: '18px', left: integrations.google ? '22px' : '3px', bottom: '3px', 
                  backgroundColor: 'white', borderRadius: '50%', transition: '0.3s' 
                }"></span>
              </span>
            </label>
          </div>

          <!-- Booking.com Toggle -->
          <div style="background: rgba(255,255,255,0.02); padding: 1.25rem; border-radius: 12px; border: 1px solid var(--card-border); display: flex; justify-content: space-between; align-items: center;">
            <div style="display: flex; align-items: center; gap: 1rem;">
              <span class="source-badge booking"><i class="fa-solid fa-b"></i></span>
              <div style="display: flex; flex-direction: column;">
                <span style="font-weight: 600; font-size: 0.9rem;">Booking.com Feed</span>
                <span style="font-size: 0.75rem; color: var(--text-muted);">Guest XML Ingestion Feed</span>
              </div>
            </div>
            <label class="switch-toggle" style="position: relative; display: inline-block; width: 44px; height: 24px;">
              <input type="checkbox" v-model="integrations.booking" style="opacity: 0; width: 0; height: 0;">
              <span class="slider-toggle" :style="{ 
                position: 'absolute', cursor: 'pointer', top: 0, left: 0, right: 0, bottom: 0, 
                backgroundColor: integrations.booking ? 'var(--success)' : 'rgba(255,255,255,0.1)', 
                borderRadius: '24px', transition: '0.3s' 
              }">
                <span :style="{ 
                  position: 'absolute', content: '', height: '18px', width: '18px', left: integrations.booking ? '22px' : '3px', bottom: '3px', 
                  backgroundColor: 'white', borderRadius: '50%', transition: '0.3s' 
                }"></span>
              </span>
            </label>
          </div>

          <!-- TripAdvisor Toggle -->
          <div style="background: rgba(255,255,255,0.02); padding: 1.25rem; border-radius: 12px; border: 1px solid var(--card-border); display: flex; justify-content: space-between; align-items: center;">
            <div style="display: flex; align-items: center; gap: 1rem;">
              <span class="source-badge tripadvisor"><i class="fa-brands fa-tripadvisor"></i></span>
              <div style="display: flex; flex-direction: column;">
                <span style="font-weight: 600; font-size: 0.9rem;">TripAdvisor Channel</span>
                <span style="font-size: 0.75rem; color: var(--text-muted);">Simulated HTML Review Scraper</span>
              </div>
            </div>
            <label class="switch-toggle" style="position: relative; display: inline-block; width: 44px; height: 24px;">
              <input type="checkbox" v-model="integrations.tripadvisor" style="opacity: 0; width: 0; height: 0;">
              <span class="slider-toggle" :style="{ 
                position: 'absolute', cursor: 'pointer', top: 0, left: 0, right: 0, bottom: 0, 
                backgroundColor: integrations.tripadvisor ? 'var(--success)' : 'rgba(255,255,255,0.1)', 
                borderRadius: '24px', transition: '0.3s' 
              }">
                <span :style="{ 
                  position: 'absolute', content: '', height: '18px', width: '18px', left: integrations.tripadvisor ? '22px' : '3px', bottom: '3px', 
                  backgroundColor: 'white', borderRadius: '50%', transition: '0.3s' 
                }"></span>
              </span>
            </label>
          </div>
        </div>
      </div>
      
      <div class="drawer-footer">
        <button @click="isIntegrationsDrawerOpen = false" class="btn-primary">Apply Settings</button>
      </div>
    </div>

    <!-- Alert Banner -->
    <div class="alert-banner" :class="[toast.type, { show: toast.show }]">
      <i :class="getToastIcon(toast.type)"></i>
      <span>{{ toast.message }}</span>
    </div>
  </div>
</template>

<script>
import { Chart, registerables } from 'chart.js';
Chart.register(...registerables);

export default {
  name: 'Dashboard',
  data() {
    return {
      reviews: [],
      kpis: {
        avg_rating: 0,
        avg_sentiment: 0,
        total_reviews: 0,
        response_rate: 0
      },
      stats: {
        sources: {},
        sentiment_history: [],
        aspects: {}
      },
      filters: {
        source: '',
        sentiment: '',
        rating: '',
        search: ''
      },
      loadingReviews: false,
      fetchingNew: false,
      generatingResponse: false,
      savingReply: false,
      isDrawerOpen: false,
      isHelpDrawerOpen: false,
      isIntegrationsDrawerOpen: false,
      integrations: {
        google: true,
        booking: true,
        tripadvisor: true
      },
      selectedReview: null,
      responseDraft: '',
      selectedTone: 'professional',
      toast: {
        message: '',
        type: 'info',
        show: false
      },
      searchTimeout: null,
      sentimentChart: null,
      sourceChart: null
    };
  },
  computed: {
    escalatedReviews() {
      return this.reviews.filter(r => r.sentiment_score <= -0.5 && r.response_status === 'pending');
    }
  },
  mounted() {
    this.fetchStats();
    this.fetchReviews();
  },
  beforeUnmount() {
    this.destroyCharts();
  },
  methods: {
    destroyCharts() {
      if (this.sentimentChart) this.sentimentChart.destroy();
      if (this.sourceChart) this.sourceChart.destroy();
    },
    
    async fetchReviews() {
      this.loadingReviews = true;
      try {
        const params = new URLSearchParams();
        if (this.filters.source) params.append('source', this.filters.source);
        if (this.filters.sentiment) params.append('sentiment', this.filters.sentiment);
        if (this.filters.rating) params.append('rating', this.filters.rating);
        if (this.filters.search) params.append('search', this.filters.search);

        const response = await fetch(`/api/reviews?${params.toString()}`);
        if (!response.ok) throw new Error('Failed to fetch reviews');
        
        this.reviews = await response.json();
      } catch (error) {
        this.showToast(error.message, 'error');
      } finally {
        this.loadingReviews = false;
      }
    },

    async fetchStats() {
      try {
        const response = await fetch('/api/stats');
        if (!response.ok) throw new Error('Failed to fetch stats');
        
        const data = await response.json();
        this.kpis = data.kpis;
        this.stats = data.charts;
        
        // Update charts on next tick
        this.$nextTick(() => {
          this.renderCharts();
        });
      } catch (error) {
        this.showToast(error.message, 'error');
      }
    },

    async fetchNewReviews() {
      this.fetchingNew = true;
      try {
        const activeSources = Object.keys(this.integrations).filter(k => this.integrations[k]).join(',');
        const response = await fetch('/api/reviews/fetch', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
          },
          body: JSON.stringify({ sources: activeSources })
        });
        
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Failed to fetch new reviews');
        
        if (data.new_count > 0) {
          this.showToast(`Imported ${data.new_count} new guest reviews!`, 'success');
          this.fetchStats();
          this.fetchReviews();
        } else {
          this.showToast('No new reviews found. Database is up to date.', 'info');
        }
      } catch (error) {
        this.showToast(error.message, 'error');
      } finally {
        this.fetchingNew = false;
      }
    },

    async openResponseDrawer(review) {
      this.selectedReview = review;
      this.isDrawerOpen = true;
      this.selectedTone = 'professional';
      
      if (review.response_status === 'replied') {
        this.responseDraft = review.reply_text || '';
        return;
      }

      this.responseDraft = '';
      await this.fetchResponseSuggestion();
    },

    async fetchResponseSuggestion() {
      this.generatingResponse = true;
      try {
        const response = await fetch(`/api/reviews/${this.selectedReview.id}/suggest-response`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
          },
          body: JSON.stringify({ tone: this.selectedTone })
        });
        
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Failed to suggest response');
        
        this.responseDraft = data.suggestion;
      } catch (error) {
        this.showToast(error.message, 'error');
        this.responseDraft = `Dear ${this.selectedReview.reviewer_name},\n\nThank you for your feedback regarding your stay.\n\nWarm regards,\nManagement`;
      } finally {
        this.generatingResponse = false;
      }
    },

    async regenerateSuggestedResponse() {
      if (!this.selectedReview) return;
      this.responseDraft = '';
      await this.fetchResponseSuggestion();
    },

    async submitReply() {
      if (!this.selectedReview) return;
      this.savingReply = true;
      try {
        const response = await fetch(`/api/reviews/${this.selectedReview.id}/reply`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
          },
          body: JSON.stringify({ reply_text: this.responseDraft })
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Failed to save reply');

        this.showToast('Reply saved and marked as replied!', 'success');
        this.closeDrawer();
        this.fetchStats();
        this.fetchReviews();
      } catch (error) {
        this.showToast(error.message, 'error');
      } finally {
        this.savingReply = false;
      }
    },

    async ignoreReview(review) {
      try {
        const response = await fetch(`/api/reviews/${review.id}/ignore`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
          }
        });

        if (!response.ok) throw new Error('Failed to ignore review');

        this.showToast('Review status updated to ignored.', 'info');
        this.fetchStats();
        this.fetchReviews();
      } catch (error) {
        this.showToast(error.message, 'error');
      }
    },

    closeDrawer() {
      this.isDrawerOpen = false;
      this.selectedReview = null;
      this.responseDraft = '';
    },

    debounceSearch() {
      clearTimeout(this.searchTimeout);
      this.searchTimeout = setTimeout(() => {
        this.fetchReviews();
      }, 350);
    },

    renderCharts() {
      this.destroyCharts();
      
      // 1. Sentiment Score Chart
      const history = this.stats.sentiment_history || [];
      if (history.length > 0 && this.$refs.sentimentChartCanvas) {
        const ctx = this.$refs.sentimentChartCanvas.getContext('2d');
        
        this.sentimentChart = new Chart(ctx, {
          type: 'line',
          data: {
            labels: history.map(h => h.date),
            datasets: [{
              label: 'Avg Sentiment',
              data: history.map(h => h.score),
              borderColor: '#6366f1',
              backgroundColor: 'rgba(99, 102, 241, 0.05)',
              borderWidth: 3,
              fill: true,
              tension: 0.35,
              pointBackgroundColor: '#a855f7',
              pointHoverRadius: 7
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false }
            },
            scales: {
              x: {
                grid: { color: 'rgba(255, 255, 255, 0.03)' },
                ticks: { color: '#94a3b8', font: { family: 'Plus Jakarta Sans' } }
              },
              y: {
                grid: { color: 'rgba(255, 255, 255, 0.03)' },
                ticks: { color: '#94a3b8', font: { family: 'Plus Jakarta Sans' } },
                min: -1.0,
                max: 1.0
              }
            }
          }
        });
      }

      // 2. Source Distribution Chart
      const sources = this.stats.sources || {};
      if (Object.keys(sources).length > 0 && this.$refs.sourceChartCanvas) {
        const ctx = this.$refs.sourceChartCanvas.getContext('2d');
        
        this.sourceChart = new Chart(ctx, {
          type: 'doughnut',
          data: {
            labels: ['Google', 'Booking.com', 'TripAdvisor'],
            datasets: [{
              data: [
                sources.google || 0,
                sources.booking || 0,
                sources.tripadvisor || 0
              ],
              backgroundColor: ['#4285f4', '#0066ff', '#00af87'],
              borderWidth: 0,
              hoverOffset: 4
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                position: 'right',
                labels: {
                  color: '#f8fafc',
                  font: { family: 'Plus Jakarta Sans', size: 12 },
                  padding: 15
                }
              }
            },
            cutout: '70%'
          }
        });
      }
    },

    // UI Helper methods
    formatDate(dateStr) {
      if (!dateStr) return '';
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      });
    },

    highlightReviewText(review) {
      const text = review.review_text;
      if (!text) return '';
      
      // Escape HTML to prevent XSS
      const tempDiv = document.createElement('div');
      tempDiv.textContent = text;
      const safeHtml = tempDiv.innerHTML;
      
      if (!review.aspect_sentiments || Object.keys(review.aspect_sentiments).length === 0) {
        return safeHtml;
      }
      
      const aspectKeywords = {
        wifi: ["wi-fi", "wifi", "internet", "connection", "router", "network", "signal", "web"],
        food: ["food", "breakfast", "dinner", "lunch", "restaurant", "meal", "delicious", "buffet", "eat", "dining", "chef", "coffee"],
        service: ["service", "staff", "reception", "bellboy", "employee", "waiter", "hospitality", "helpful", "friendly", "rude", "desk", "host"],
        room: ["room", "bed", "bathroom", "shower", "aircon", "ac", "sheets", "pillow", "noise", "sleep", "suite"],
        cleanliness: ["cleanliness", "clean", "dirty", "dust", "spotless", "hygiene", "messy", "smell", "neat", "spotted", "filthy"],
        price: ["price", "cost", "expensive", "value", "cheap", "worth", "affordable", "pricey", "charge", "fee"]
      };

      const matches = [];
      
      for (const [aspect, keywords] of Object.entries(aspectKeywords)) {
        const sentiment = review.aspect_sentiments[aspect];
        if (!sentiment) continue;
        
        const hlClass = `hl-${sentiment}`;
        
        for (const keyword of keywords) {
          const regex = new RegExp(`\\b${keyword}\\b`, 'gi');
          let match;
          while ((match = regex.exec(safeHtml)) !== null) {
            matches.push({
              start: match.index,
              end: match.index + match[0].length,
              hlClass: hlClass,
              aspect: aspect
            });
          }
        }
      }
      
      if (matches.length === 0) return safeHtml;
      
      // Sort matches to prevent overlaps
      matches.sort((a, b) => (a.start - b.start) || (b.end - a.end));
      const nonOverlapping = [];
      let lastEnd = -1;
      for (const match of matches) {
        if (match.start >= lastEnd) {
          nonOverlapping.push(match);
          lastEnd = match.end;
        }
      }
      
      // Build highlighted text
      let result = '';
      let cursor = 0;
      for (const match of nonOverlapping) {
        result += safeHtml.substring(cursor, match.start);
        const matchedText = safeHtml.substring(match.start, match.end);
        result += `<span class="highlight-word ${match.hlClass}" title="${match.aspect === 'wifi' ? 'Wi-Fi' : match.aspect}: ${match.hlClass.replace('hl-', '')}">${matchedText}</span>`;
        cursor = match.end;
      }
      result += safeHtml.substring(cursor);
      
      return result;
    },

    getSourceIcon(source) {
      if (source === 'google') return 'fa-brands fa-google';
      if (source === 'booking') return 'fa-solid fa-b';
      return 'fa-brands fa-tripadvisor';
    },

    getSentimentClass(score) {
      if (score >= 0.15) return 'success';
      if (score <= -0.15) return 'danger';
      return 'info';
    },

    getAspectPercentage(val, counts) {
      const total = (counts.positive || 0) + (counts.negative || 0) + (counts.neutral || 0);
      if (total === 0) return 0;
      return (val / total) * 100;
    },

    showToast(message, type = 'info') {
      this.toast.message = message;
      this.toast.type = type;
      this.toast.show = true;
      setTimeout(() => {
        this.toast.show = false;
      }, 4000);
    },

    getToastIcon(type) {
      if (type === 'success') return 'fa-solid fa-circle-check';
      if (type === 'error') return 'fa-solid fa-circle-exclamation';
      return 'fa-solid fa-circle-info';
    },

    truncateText(text, length) {
      if (!text) return '';
      return text.length > length ? text.substring(0, length) + '...' : text;
    }
  }
};
</script>
