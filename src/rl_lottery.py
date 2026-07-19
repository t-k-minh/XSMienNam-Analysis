"""Reinforcement Learning for XSMN Lottery Prediction."""
import json
import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict
import random

# Load data
data = json.loads(Path('data/xsmn.json').read_text())
df = pd.DataFrame(data)
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(['province', 'date'])

print('='*70)
print('REINFORCEMENT LEARNING FOR XSMN LOTTERY')
print('='*70)
print(f'Data: {len(df)} records, {df["province"].nunique()} provinces')
print()

# Use TP.HCM
hcm_data = df[df['province'] == 'HCM'].sort_values('date')
print(f'TP.HCM: {len(hcm_data)} records')
print()

# Extract targets
targets = []
for _, row in hcm_data.iterrows():
    val = row['special']
    if pd.notna(val):
        targets.append(int(str(val)[-2:]))
    else:
        targets.append(0)

# ============================================================
# METHOD 1: MULTI-ARMED BANDIT (Thompson Sampling)
# ============================================================
print('=== METHOD 1: THOMPSON SAMPLING ===')
print()

class ThompsonSampling:
    """Thompson Sampling for lottery number selection."""
    def __init__(self, n_arms=100, alpha=1.0, beta=1.0):
        self.n_arms = n_arms
        self.alpha = np.ones(n_arms) * alpha  # Success count
        self.beta = np.ones(n_arms) * beta    # Failure count

    def update(self, chosen, reward):
        """Update beliefs based on reward."""
        if reward > 0:
            self.alpha[chosen] += 1
        else:
            self.beta[chosen] += 1

    def sample(self, n=6):
        """Sample n arms based on current beliefs."""
        # Sample from Beta distribution for each arm
        samples = np.random.beta(self.alpha, self.beta)
        # Select top n
        return set(np.argsort(samples)[-n:])

    def get_probs(self):
        """Get expected probability for each arm."""
        return self.alpha / (self.alpha + self.beta)

# Run Thompson Sampling
ts = ThompsonSampling(n_arms=100)
ts_rewards = []
ts_predictions = []

for i in range(30, len(targets)):
    # Get prediction
    predicted = ts.sample(6)
    actual = targets[i]
    ts_predictions.append(predicted)

    # Update based on reward (1 if actual in predicted, 0 otherwise)
    reward = 1 if actual in predicted else 0
    ts_rewards.append(reward)

    # Update all arms that were chosen
    for arm in predicted:
        ts.update(arm, 1 if arm == actual else 0)

ts_accuracy = np.mean(ts_rewards) * 100
print(f'Thompson Sampling Accuracy: {ts_accuracy:.2f}%')
print(f'Random baseline: 6.00%')
print()

# Show learned probabilities
probs = ts.get_probs()
top20 = np.argsort(probs)[-20:][::-1]
print('Top 20 learned probabilities:')
for arm in top20:
    print(f'  Number {arm:2d}: {probs[arm]:.4f}')
print()

# ============================================================
# METHOD 2: Q-LEARNING
# ============================================================
print('=== METHOD 2: Q-LEARNING ===')
print()

class QLearning:
    """Q-Learning for lottery number selection."""
    def __init__(self, n_states=100, n_actions=100, lr=0.1, gamma=0.9, epsilon=0.1):
        self.n_states = n_states
        self.n_actions = n_actions
        self.lr = lr
        self.gamma = gamma
        self.epsilon = epsilon
        self.q_table = np.zeros((n_states, n_actions))

    def get_state(self, recent_numbers):
        """Get state based on recent numbers."""
        if not recent_numbers:
            return 0
        return recent_numbers[-1] % self.n_states

    def choose_action(self, state, n=6):
        """Choose n actions (numbers) using epsilon-greedy."""
        if random.random() < self.epsilon:
            # Explore: random selection
            return set(random.sample(range(self.n_actions), n))
        else:
            # Exploit: select top n Q-values
            q_values = self.q_table[state]
            return set(np.argsort(q_values)[-n:])

    def update(self, state, actions, reward, next_state):
        """Update Q-table."""
        for action in actions:
            old_q = self.q_table[state, action]
            next_max = np.max(self.q_table[next_state])
            new_q = old_q + self.lr * (reward + self.gamma * next_max - old_q)
            self.q_table[state, action] = new_q

# Run Q-Learning
ql = QLearning(n_states=100, n_actions=100, lr=0.1, gamma=0.9, epsilon=0.2)
ql_rewards = []
ql_predictions = []

for i in range(30, len(targets)):
    state = ql.get_state(targets[max(0, i-5):i])  # Last 5 numbers
    predicted = ql.choose_action(state, n=6)
    actual = targets[i]
    ql_predictions.append(predicted)

    # Reward: 1 if actual in predicted, 0 otherwise
    reward = 1 if actual in predicted else 0
    ql_rewards.append(reward)

    # Update Q-table
    next_state = actual
    ql.update(state, predicted, reward, next_state)

ql_accuracy = np.mean(ql_rewards) * 100
print(f'Q-Learning Accuracy: {ql_accuracy:.2f}%')
print(f'Random baseline: 6.00%')
print()

# ============================================================
# METHOD 3: SARSA (State-Action-Reward-State-Action)
# ============================================================
print('=== METHOD 3: SARSA ===')
print()

class SARSA:
    """SARSA for lottery number selection."""
    def __init__(self, n_states=100, n_actions=100, lr=0.1, gamma=0.9, epsilon=0.1):
        self.n_states = n_states
        self.n_actions = n_actions
        self.lr = lr
        self.gamma = gamma
        self.epsilon = epsilon
        self.q_table = np.zeros((n_states, n_actions))

    def get_state(self, recent_numbers):
        if not recent_numbers:
            return 0
        return recent_numbers[-1] % self.n_states

    def choose_action(self, state, n=6):
        if random.random() < self.epsilon:
            return set(random.sample(range(self.n_actions), n))
        else:
            q_values = self.q_table[state]
            return set(np.argsort(q_values)[-n:])

    def update(self, state, actions, reward, next_state, next_actions):
        """SARSA update using next action."""
        for action in actions:
            old_q = self.q_table[state, action]
            # Use expected value of next action
            next_q = np.mean([self.q_table[next_state, a] for a in next_actions])
            new_q = old_q + self.lr * (reward + self.gamma * next_q - old_q)
            self.q_table[state, action] = new_q

# Run SARSA
sarsa = SARSA(n_states=100, n_actions=100, lr=0.1, gamma=0.9, epsilon=0.2)
sarsa_rewards = []

for i in range(30, len(targets)):
    state = sarsa.get_state(targets[max(0, i-5):i])
    predicted = sarsa.choose_action(state, n=6)
    actual = targets[i]

    reward = 1 if actual in predicted else 0
    sarsa_rewards.append(reward)

    # Get next action for SARSA update
    next_state = actual
    next_actions = sarsa.choose_action(next_state, n=6)
    sarsa.update(state, predicted, reward, next_state, next_actions)

sarsa_accuracy = np.mean(sarsa_rewards) * 100
print(f'SARSA Accuracy: {sarsa_accuracy:.2f}%')
print(f'Random baseline: 6.00%')
print()

# ============================================================
# METHOD 4: MONTE CARLO RL
# ============================================================
print('=== METHOD 4: MONTE CARLO RL ===')
print()

class MonteCarloRL:
    """Monte Carlo RL for lottery prediction."""
    def __init__(self, n_states=100, n_actions=100, gamma=0.9):
        self.n_states = n_states
        self.n_actions = n_actions
        self.gamma = gamma
        self.returns = defaultdict(list)
        self.q_table = np.zeros((n_states, n_actions))

    def get_state(self, recent_numbers):
        if not recent_numbers:
            return 0
        return recent_numbers[-1] % self.n_states

    def choose_action(self, state, n=6):
        # Use current Q-values
        q_values = self.q_table[state]
        return set(np.argsort(q_values)[-n:])

    def update(self, episode):
        """Update Q-values from episode."""
        G = 0
        for state, action, reward in reversed(episode):
            G = reward + self.gamma * G
            action_key = tuple(sorted(action))  # Convert set to tuple for hashing
            self.returns[(state, action_key)].append(G)
            self.q_table[state, action_key] = np.mean(self.returns[(state, action_key)])

# Run Monte Carlo RL
mc = MonteCarloRL(n_states=100, n_actions=100, gamma=0.9)
mc_rewards = []
mc_episode = []

for i in range(30, len(targets)):
    state = mc.get_state(targets[max(0, i-5):i])
    predicted = mc.choose_action(state, n=6)
    actual = targets[i]

    reward = 1 if actual in predicted else 0
    mc_rewards.append(reward)

    # Add to episode
    mc_episode.append((state, predicted, reward))

    # Update every 10 steps
    if len(mc_episode) >= 10:
        mc.update(mc_episode)
        mc_episode = []

mc_accuracy = np.mean(mc_rewards) * 100
print(f'Monte Carlo RL Accuracy: {mc_accuracy:.2f}%')
print(f'Random baseline: 6.00%')
print()

# ============================================================
# METHOD 5: Q-LEARNING with Feature State
# ============================================================
print('=== METHOD 5: Q-LEARNING (Feature State) ===')
print()

class QLearningFeature:
    """Q-Learning with feature-based state."""
    def __init__(self, n_actions=100, lr=0.1, gamma=0.9, epsilon=0.1):
        self.n_actions = n_actions
        self.lr = lr
        self.gamma = gamma
        self.epsilon = epsilon
        self.q_table = defaultdict(lambda: np.zeros(n_actions))

    def get_state_features(self, recent_numbers):
        """Extract features from recent numbers."""
        if not recent_numbers:
            return (0, 0, 0, 0)  # Default state

        # Features: mean, std, min, max of last 5 numbers
        last5 = recent_numbers[-5:] if len(recent_numbers) >= 5 else recent_numbers
        mean_val = np.mean(last5)
        std_val = np.std(last5) if len(last5) > 1 else 0
        min_val = min(last5)
        max_val = max(last5)

        # Discretize
        state = (
            int(mean_val / 20),  # 0-4
            int(std_val / 10),   # 0-4
            int(min_val / 20),   # 0-4
            int(max_val / 20)    # 0-4
        )
        return state

    def choose_action(self, state, n=6):
        if random.random() < self.epsilon:
            return set(random.sample(range(self.n_actions), n))
        else:
            q_values = self.q_table[state]
            return set(np.argsort(q_values)[-n:])

    def update(self, state, actions, reward, next_state):
        for action in actions:
            old_q = self.q_table[state][action]
            next_max = np.max(self.q_table[next_state])
            new_q = old_q + self.lr * (reward + self.gamma * next_max - old_q)
            self.q_table[state][action] = new_q

# Run Q-Learning with features
qlf = QLearningFeature(n_actions=100, lr=0.1, gamma=0.9, epsilon=0.2)
qlf_rewards = []

for i in range(30, len(targets)):
    state = qlf.get_state_features(targets[max(0, i-5):i])
    predicted = qlf.choose_action(state, n=6)
    actual = targets[i]

    reward = 1 if actual in predicted else 0
    qlf_rewards.append(reward)

    next_state = qlf.get_state_features(targets[max(0, i-4):i+1])
    qlf.update(state, predicted, reward, next_state)

qlf_accuracy = np.mean(qlf_rewards) * 100
print(f'Q-Learning (Feature) Accuracy: {qlf_accuracy:.2f}%')
print(f'Random baseline: 6.00%')
print()

# ============================================================
# RESULTS COMPARISON
# ============================================================
print('='*70)
print('RESULTS COMPARISON')
print('='*70)
print()

results = {
    'Thompson Sampling': ts_accuracy,
    'Q-Learning': ql_accuracy,
    'SARSA': sarsa_accuracy,
    'Monte Carlo RL': mc_accuracy,
    'Q-Learning (Feature)': qlf_accuracy,
    'Random': 6.0,
}

print(f'{"Method":<25} {"Accuracy":<12} {"vs Random (6%)":<15} {"Verdict"}')
print('-' * 65)

for name, acc in sorted(results.items(), key=lambda x: x[1], reverse=True):
    diff = acc - 6.0
    verdict = 'CO EDGE' if acc > 7 else ('BANG' if acc > 5.5 else 'KEM HON')
    print(f'{name:<25} {acc:.2f}%{" ":<5} {diff:+.2f}%{" ":<8} {verdict}')

print('-' * 65)
print()

# ============================================================
# ANALYSIS
# ============================================================
print('='*70)
print('PHAN TICH')
print('='*70)
print()

best_method = max(results.items(), key=lambda x: x[1])
worst_method = min(results.items(), key=lambda x: x[1])

print(f'Phuong phap tot nhat: {best_method[0]} ({best_method[1]:.2f}%)')
print(f'Phuong phap kem nhat: {worst_method[0]} ({worst_method[1]:.2f}%)')
print()

if best_method[1] > 7:
    print(f'Ket luan: {best_method[0]} co EDGE nho ({best_method[1]:.2f}% vs 6.00% random)')
else:
    print('Ket luan: KHONG co phuong phap RL nao co EDGE ro rang')
    print('Tat ca deu ~ 6% (ngau nhien)')

print()
print('='*70)
print('REINFORCEMENT LEARNING INSIGHTS')
print('='*70)
print()
print('1. Thompson Sampling: Hoc xac suat tung so, chon so co xac suat cao nhat')
print('2. Q-Learning: Hoc gia tri cua moi hanh dong trong moi trang thai')
print('3. SARSA: Cap nhat Q-value theo hanh dong thuc te')
print('4. Monte Carlo: Hoc tu toan bo episode')
print('5. Q-Learning (Feature): Su dung feature-based state representation')
print()
print('Ket qua cho thay: RL cung KHONG tim duoc pattern trong xo so')
print('Ly do: XO SO LA NGAU NHIEN - khong co state nao thuc su ton tai')
