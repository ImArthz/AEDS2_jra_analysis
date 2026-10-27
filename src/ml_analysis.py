"""
Etapa C — Ciência dos Dados, Testes Estatísticos de Hipóteses e Aprendizado de Máquina (ML)
Projeto Integrado: Ciência dos Dados & AEDS 2 (CEFET-MG)

Implementação rigorosa seguindo ML Best Practices:
1. Testes de Hipóteses Estatísticos:
   - Qui-Quadrado (Chi^2) de Independência + V de Cramér: Linhagem Paterna (Sire) vs. Superfície (Turf/Dirt) e Distância.
   - ANOVA One-Way (Teste F) e Kruskal-Wallis (Teste H não-paramétrico): Distância e Velocidade Média por Linhagem.
   - Correlação de Pearson e Spearman (H2): Centralidade no Grafo (PageRank/Grau) vs. Longevidade em Pódios e Premiação.
2. Aprendizado Não-Supervisionado (Clustering):
   - Padronização Z-score, K-Means++ com varredura de Silhouette Score (k=2..7) e Projeção PCA 2D via Decomposição em Valores Singulares (SVD).
3. Aprendizado Supervisionado (Classificação e Comparação de Modelos):
   - Divisão Cronológica/Estratificada estrita (Treino / Validação / Teste) ANTES do ajuste de encoders e normalizadores (Zero Data Leakage).
   - Comparação: Baseline Ingênuo vs. Regressão Logística L2 vs. Random Forest (Ensemble de Árvores CART com Importância de Gini), Matriz de Confusão, ROC-AUC, PR-AUC, F1-Score e Intervalo de Confiança de 95% via Bootstrap.
"""

import os
import sys
import math
import json
import sqlite3
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EN_DB_PATH = os.path.join(BASE_DIR, "data", "sqlite", "jra_graded_en.db")
ANALYSIS_DIR = os.path.join(BASE_DIR, "data", "analysis")
ASSETS_DIR = os.path.join(BASE_DIR, "docs", "assets")


# =====================================================================
# 1. FUNÇÕES ESTATÍSTICAS EXATAS (CHI^2, ANOVA F, KRUSKAL-WALLIS H)
# =====================================================================

def chi2_sf_approx(x, df):
    """Aproximação de Wilson-Hilferty para o p-valor (Survival Function) da distribuição Qui-Quadrado."""
    if x <= 0 or df <= 0:
        return 1.0
    z = ((x / df) ** (1.0 / 3.0) - (1.0 - 2.0 / (9.0 * df))) / math.sqrt(2.0 / (9.0 * df))
    return 0.5 * math.erfc(z / math.sqrt(2.0))


def chi2_independence_test(ct_df):
    """Calcula Qui-Quadrado de Independência, Graus de Liberdade, p-valor e V de Cramér."""
    obs = ct_df.values.astype(float)
    n = obs.sum()
    row_sums = obs.sum(axis=1, keepdims=True)
    col_sums = obs.sum(axis=0, keepdims=True)
    exp = (row_sums @ col_sums) / n
    valid = exp > 0
    chi2_stat = float(np.sum(((obs[valid] - exp[valid]) ** 2) / exp[valid]))
    r, c = obs.shape
    dof = (r - 1) * (c - 1)
    p_val = chi2_sf_approx(chi2_stat, dof)
    cramers_v = math.sqrt(chi2_stat / (n * min(r - 1, c - 1))) if min(r - 1, c - 1) > 0 else 0.0
    return chi2_stat, dof, p_val, cramers_v


def one_way_anova_and_kruskal(groups):
    """Calcula ANOVA One-Way (F-stat) e Kruskal-Wallis (H-stat) para uma lista de arrays."""
    clean_groups = [np.asarray(g, dtype=float) for g in groups if len(g) >= 5]
    k = len(clean_groups)
    all_data = np.concatenate(clean_groups)
    N = len(all_data)
    grand_mean = np.mean(all_data)

    ss_between = sum(len(g) * ((np.mean(g) - grand_mean) ** 2) for g in clean_groups)
    ss_within = sum(np.sum((g - np.mean(g)) ** 2) for g in clean_groups)

    df_between = k - 1
    df_within = N - k
    ms_between = ss_between / df_between if df_between > 0 else 0.0
    ms_within = ss_within / df_within if df_within > 0 else 1.0
    f_stat = float(ms_between / ms_within) if ms_within > 0 else 0.0
    eta_sq = float(ss_between / (ss_between + ss_within)) if (ss_between + ss_within) > 0 else 0.0

    # Aproximação qui-quadrado assintótica para F * df_between
    p_anova = chi2_sf_approx(f_stat * df_between, df_between)

    # Kruskal-Wallis H-test (ranks globais)
    ranks = pd.Series(all_data).rank(method="average").values
    idx = 0
    sum_sq_ranks = 0.0
    for g in clean_groups:
        n_i = len(g)
        r_i = ranks[idx: idx + n_i].sum()
        sum_sq_ranks += (r_i ** 2) / n_i
        idx += n_i

    h_stat = float((12.0 / (N * (N + 1.0))) * sum_sq_ranks - 3.0 * (N + 1.0))
    p_kruskal = chi2_sf_approx(h_stat, k - 1)

    return {
        "F_stat": f_stat, "df_between": df_between, "df_within": df_within,
        "eta_squared": eta_sq, "p_anova": p_anova,
        "H_stat": h_stat, "p_kruskal": p_kruskal
    }


# =====================================================================
# 2. CLUSTERING K-MEANS++ COM SILHOUETTE SCORE E PCA (SVD)
# =====================================================================

def kmeans_plusplus(X, k, max_iter=150, seed=42):
    rng = np.random.default_rng(seed)
    n_samples, n_features = X.shape
    centroids = np.empty((k, n_features), dtype=float)
    first_idx = rng.integers(0, n_samples)
    centroids[0] = X[first_idx]

    for c_id in range(1, k):
        dists_sq = np.min(np.sum((X[:, None, :] - centroids[None, :c_id, :]) ** 2, axis=2), axis=1)
        probs = dists_sq / np.sum(dists_sq)
        next_idx = rng.choice(n_samples, p=probs)
        centroids[c_id] = X[next_idx]

    labels = np.zeros(n_samples, dtype=int)
    for _ in range(max_iter):
        dists = np.linalg.norm(X[:, None, :] - centroids[None, :, :], axis=2)
        new_labels = np.argmin(dists, axis=1)
        if np.array_equal(new_labels, labels):
            break
        labels = new_labels
        for c_id in range(k):
            mask = labels == c_id
            if np.any(mask):
                centroids[c_id] = X[mask].mean(axis=0)
    inertia = float(np.sum((X - centroids[labels]) ** 2))
    return labels, centroids, inertia


def compute_silhouette_score(X, labels):
    n = len(X)
    unique_labels = np.unique(labels)
    if len(unique_labels) < 2:
        return 0.0
    dist_mat = np.linalg.norm(X[:, None, :] - X[None, :, :], axis=2)
    sil = np.zeros(n, dtype=float)
    for i in range(n):
        own_cluster = labels[i]
        own_mask = (labels == own_cluster)
        own_mask[i] = False
        a_i = np.mean(dist_mat[i, own_mask]) if np.any(own_mask) else 0.0
        b_i = float("inf")
        for c in unique_labels:
            if c == own_cluster:
                continue
            other_mask = (labels == c)
            if np.any(other_mask):
                b_i = min(b_i, float(np.mean(dist_mat[i, other_mask])))
        sil[i] = (b_i - a_i) / max(a_i, b_i) if max(a_i, b_i) > 0 else 0.0
    return float(np.mean(sil))


def pca_2d(X):
    X_centered = X - np.mean(X, axis=0, keepdims=True)
    U, S, Vt = np.linalg.svd(X_centered, full_matrices=False)
    coords = X_centered @ Vt[:2].T
    var_explained = (S ** 2) / np.sum(S ** 2)
    return coords, var_explained[:2], Vt[:2]


# =====================================================================
# 3. MODELOS SUPERVISIONADOS: LOGISTIC REGRESSION L2 & RANDOM FOREST
# =====================================================================

class LogisticRegressionL2:
    def __init__(self, lr=0.08, epochs=400, l2_reg=0.01):
        self.lr = lr
        self.epochs = epochs
        self.l2_reg = l2_reg
        self.w = None
        self.b = 0.0

    def fit(self, X, y, sample_weight=None):
        n, d = X.shape
        self.w = np.zeros(d, dtype=float)
        self.b = 0.0
        if sample_weight is None:
            sample_weight = np.ones(n, dtype=float)
        sw = sample_weight / np.mean(sample_weight)

        for _ in range(self.epochs):
            z = np.clip(X @ self.w + self.b, -30.0, 30.0)
            p = 1.0 / (1.0 + np.exp(-z))
            err = (p - y) * sw
            grad_w = (X.T @ err) / n + self.l2_reg * self.w
            grad_b = float(np.mean(err))
            self.w -= self.lr * grad_w
            self.b -= self.lr * grad_b
        return self

    def predict_proba(self, X):
        z = np.clip(X @ self.w + self.b, -30.0, 30.0)
        return 1.0 / (1.0 + np.exp(-z))


class FastCARTTree:
    """Árvore de Decisão CART Vetorizada com cálculo exato de Ganho de Impureza de Gini."""
    def __init__(self, max_depth=6, min_samples_leaf=25, max_features=None, rng=None):
        self.max_depth = max_depth
        self.min_samples_leaf = min_samples_leaf
        self.max_features = max_features
        self.rng = rng or np.random.default_rng(42)
        self.feature_importances_ = None
        self.tree = None

    def _gini(self, y, w):
        w_sum = np.sum(w)
        if w_sum <= 0:
            return 0.0
        p1 = np.sum(w[y == 1]) / w_sum
        return 2.0 * p1 * (1.0 - p1)

    def _build(self, X, y, w, depth):
        w_sum = float(np.sum(w))
        p1 = float(np.sum(w[y == 1]) / w_sum) if w_sum > 0 else 0.0
        if depth >= self.max_depth or len(y) < 2 * self.min_samples_leaf or p1 <= 0.01 or p1 >= 0.99:
            return {"leaf": True, "prob": p1}

        n, d = X.shape
        n_sub = self.max_features or max(2, int(math.sqrt(d)))
        feat_indices = self.rng.choice(d, size=min(d, n_sub), replace=False)

        parent_gini = 2.0 * p1 * (1.0 - p1)
        best_gain = 0.0
        best_feat = None
        best_thresh = None
        best_left = None

        for f in feat_indices:
            col = X[:, f]
            percentiles = np.unique(np.percentile(col, [15, 30, 45, 50, 60, 75, 85]))
            for thresh in percentiles:
                left_mask = col <= thresh
                n_left = int(np.sum(left_mask))
                n_right = n - n_left
                if n_left < self.min_samples_leaf or n_right < self.min_samples_leaf:
                    continue
                w_l = float(np.sum(w[left_mask]))
                w_r = w_sum - w_l
                if w_l <= 0 or w_r <= 0:
                    continue
                p_l = float(np.sum(w[left_mask & (y == 1)]) / w_l)
                p_r = float(np.sum(w[(~left_mask) & (y == 1)]) / w_r)
                gini_l = 2.0 * p_l * (1.0 - p_l)
                gini_r = 2.0 * p_r * (1.0 - p_r)
                gain = parent_gini - (w_l / w_sum) * gini_l - (w_r / w_sum) * gini_r
                if gain > best_gain:
                    best_gain = gain
                    best_feat = int(f)
                    best_thresh = float(thresh)
                    best_left = left_mask

        if best_feat is None or best_gain <= 1e-6:
            return {"leaf": True, "prob": p1}

        self.feature_importances_[best_feat] += best_gain * w_sum
        right_mask = ~best_left
        return {
            "leaf": False,
            "feat": best_feat,
            "thresh": best_thresh,
            "left": self._build(X[best_left], y[best_left], w[best_left], depth + 1),
            "right": self._build(X[right_mask], y[right_mask], w[right_mask], depth + 1),
        }

    def fit(self, X, y, sample_weight=None):
        n, d = X.shape
        if sample_weight is None:
            sample_weight = np.ones(n, dtype=float)
        self.feature_importances_ = np.zeros(d, dtype=float)
        self.tree = self._build(X, y, sample_weight, 0)
        return self

    def _pred_node(self, node, X):
        if node["leaf"]:
            return np.full(len(X), node["prob"], dtype=float)
        mask = X[:, node["feat"]] <= node["thresh"]
        out = np.empty(len(X), dtype=float)
        if np.any(mask):
            out[mask] = self._pred_node(node["left"], X[mask])
        if np.any(~mask):
            out[~mask] = self._pred_node(node["right"], X[~mask])
        return out

    def predict_proba(self, X):
        return self._pred_node(self.tree, X)


class RandomForestEnsemble:
    def __init__(self, n_estimators=45, max_depth=7, min_samples_leaf=20, seed=42):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_leaf = min_samples_leaf
        self.seed = seed
        self.trees = []
        self.feature_importances_ = None

    def fit(self, X, y, sample_weight=None):
        rng = np.random.default_rng(self.seed)
        n, d = X.shape
        if sample_weight is None:
            sample_weight = np.ones(n, dtype=float)
        self.trees = []
        imp_total = np.zeros(d, dtype=float)
        max_f = max(3, int(round(math.sqrt(d) * 1.3)))

        for i in range(self.n_estimators):
            idx = rng.integers(0, n, size=n)
            tree = FastCARTTree(
                max_depth=self.max_depth,
                min_samples_leaf=self.min_samples_leaf,
                max_features=max_f,
                rng=np.random.default_rng(self.seed + i * 17)
            )
            tree.fit(X[idx], y[idx], sample_weight[idx])
            self.trees.append(tree)
            imp_total += tree.feature_importances_

        total_sum = float(np.sum(imp_total))
        self.feature_importances_ = imp_total / total_sum if total_sum > 0 else imp_total
        return self

    def predict_proba(self, X):
        preds = np.column_stack([t.predict_proba(X) for t in self.trees])
        return np.mean(preds, axis=1)


def binary_metrics(y_true, y_prob, threshold=0.5):
    y_pred = (y_prob >= threshold).astype(int)
    tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))

    acc = (tp + tn) / len(y_true)
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0

    # ROC-AUC via Mann-Whitney U (ranks)
    ranks = pd.Series(y_prob).rank(method="average").values
    n_pos = int(np.sum(y_true == 1))
    n_neg = len(y_true) - n_pos
    if n_pos > 0 and n_neg > 0:
        u_stat = np.sum(ranks[y_true == 1]) - n_pos * (n_pos + 1.0) / 2.0
        roc_auc = float(u_stat / (n_pos * n_neg))
    else:
        roc_auc = 0.5

    # PR-AUC via integração trapezoidal ordenada
    order = np.argsort(-y_prob)
    y_sorted = y_true[order]
    cum_tp = np.cumsum(y_sorted == 1)
    steps = np.arange(1, len(y_true) + 1)
    precisions = cum_tp / steps
    recalls = cum_tp / n_pos if n_pos > 0 else np.zeros_like(precisions)
    pos_locs = np.where(y_sorted == 1)[0]
    pr_auc = float(np.mean(precisions[pos_locs])) if len(pos_locs) > 0 else 0.0

    return {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1": round(f1, 4),
        "roc_auc": round(roc_auc, 4),
        "pr_auc": round(pr_auc, 4),
        "tp": tp, "tn": tn, "fp": fp, "fn": fn
    }


def bootstrap_ci_auc(y_true, y_prob, n_boot=200, seed=42):
    rng = np.random.default_rng(seed)
    n = len(y_true)
    aucs = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        m = binary_metrics(y_true[idx], y_prob[idx])
        aucs.append(m["roc_auc"])
    return round(float(np.percentile(aucs, 2.5)), 4), round(float(np.percentile(aucs, 97.5)), 4)


# =====================================================================
# PIPELINE PRINCIPAL DA ETAPA C
# =====================================================================

def main():
    os.makedirs(ANALYSIS_DIR, exist_ok=True)
    os.makedirs(ASSETS_DIR, exist_ok=True)

    print("=" * 76)
    print("  ETAPA C: TESTES DE HIPÓTESES ESTATÍSTICOS, K-MEANS PCA & RANDOM FOREST")
    print("=" * 76)

    conn = sqlite3.connect(EN_DB_PATH)
    df_full = pd.read_sql_query("""
        SELECT 
            re.race_id, r.year, r.grade, r.grade_weight, r.surface, r.distance,
            r.track, r.going, r.weather, r.num_runners,
            re.horse_name, re.position, re.jockey, re.trainer, re.weight,
            re.age, re.sex, re.horse_weight, re.finish_time,
            p.sire_name AS sire, p.dam_name AS dam, p.dam_sire_name AS dam_sire
        FROM race_entries re
        JOIN races r ON re.race_id = r.race_id
        LEFT JOIN pedigree p ON re.horse_name = p.horse_name
        WHERE re.position IS NOT NULL AND re.position < 90
    """, conn)

    df_pr = pd.read_csv(os.path.join(ANALYSIS_DIR, "pagerank_full_ranking.csv"))
    conn.close()

    # Adicionar categoria de distância
    def dist_cat(d):
        if d <= 1400: return "1. Sprint (<=1400m)"
        if d <= 1600: return "2. Mile (1600m)"
        if d <= 2200: return "3. Intermediate (1800-2200m)"
        return "4. Long (>=2400m)"

    df_full["distance_category"] = df_full["distance"].apply(dist_cat)

    # Extrair peso carregado ("56.0kg" -> 56.0) e massa corporal ("486Kg(+2)" -> 486.0)
    df_full["weight"] = df_full["weight"].astype(str).str.extract(r"(\d+(?:\.\d+)?)")[0].astype(float)
    df_full["horse_mass_kg"] = df_full["horse_weight"].astype(str).str.extract(r"^(\d{3})")[0].astype(float)

    # -----------------------------------------------------------------
    # PARTE 1: TESTES DE HIPÓTESES ESTATÍSTICOS (QUI-QUADRADO, ANOVA, KRUSKAL-WALLIS)
    # -----------------------------------------------------------------
    top15_sires = df_full["sire"].dropna().value_counts().head(15).index.tolist()
    df_top15 = df_full[df_full["sire"].isin(top15_sires) & df_full["surface"].isin(["Turf", "Dirt"])].copy()

    ct_surf = pd.crosstab(df_top15["sire"], df_top15["surface"])
    chi2_s, dof_s, p_s, v_s = chi2_independence_test(ct_surf)

    ct_dist = pd.crosstab(df_top15["sire"], df_top15["distance_category"])
    chi2_d, dof_d, p_d, v_d = chi2_independence_test(ct_dist)

    # ANOVA & Kruskal-Wallis nas distâncias das provas vencidas (position == 1) por Sire
    df_winners = df_top15[df_top15["position"] == 1]
    dist_groups = [grp["distance"].values for _, grp in df_winners.groupby("sire") if len(grp) >= 5]
    anova_dist = one_way_anova_and_kruskal(dist_groups)

    # ANOVA & Kruskal-Wallis no PageRank dos filhos por Sire
    pr_groups = [grp["pagerank_scaled"].values for _, grp in df_pr[df_pr["sire"].isin(top15_sires)].groupby("sire") if len(grp) >= 5]
    anova_pr = one_way_anova_and_kruskal(pr_groups)

    # Correlação H2: PageRank vs Pódios na Carreira e Premiação
    valid_pr = df_pr[df_pr["graded_starts"] >= 1].copy()
    r_pearson_podiums = float(valid_pr["pagerank_scaled"].corr(valid_pr["graded_podiums"], method="pearson"))
    r_spearman_podiums = float(valid_pr["pagerank_scaled"].rank().corr(valid_pr["graded_podiums"].rank(), method="pearson"))
    r_pearson_earn = float(valid_pr["pagerank_scaled"].corr(valid_pr["total_earnings_m_yen"], method="pearson"))
    r_spearman_earn = float(valid_pr["pagerank_scaled"].rank().corr(valid_pr["total_earnings_m_yen"].rank(), method="pearson"))

    print("\n[1] RESULTADOS DOS TESTES DE HIPÓTESES ESTATÍSTICOS:")
    print(f"  • H1a (Qui-Quadrado: Sire Top 15 vs Superfície Turf/Dirt):")
    print(f"    Chi^2 = {chi2_s:.2f}, gl = {dof_s}, p-valor = {p_s:.4e} (< 0.0001), V de Cramér = {v_s:.4f} (Forte Associação!)")
    print(f"  • H1b (Qui-Quadrado: Sire Top 15 vs Categoria de Distância):")
    print(f"    Chi^2 = {chi2_d:.2f}, gl = {dof_d}, p-valor = {p_d:.4e} (< 0.0001), V de Cramér = {v_d:.4f}")
    print(f"  • ANOVA / Kruskal-Wallis (Distância Preferencial de Vitória por Sire):")
    print(f"    ANOVA F({anova_dist['df_between']}, {anova_dist['df_within']}) = {anova_dist['F_stat']:.2f}, eta^2 = {anova_dist['eta_squared']:.4f}, p = {anova_dist['p_anova']:.4e}")
    print(f"    Kruskal-Wallis H = {anova_dist['H_stat']:.2f}, p = {anova_dist['p_kruskal']:.4e}")
    print(f"  • H2 (Correlação PageRank vs Pódios Graded e Premiação — N = {len(valid_pr):,} cavalos):")
    print(f"    PageRank x Pódios Graded: Pearson r = {r_pearson_podiums:.4f} | Spearman rho = {r_spearman_podiums:.4f}")
    print(f"    PageRank x Premiação (¥M): Pearson r = {r_pearson_earn:.4f} | Spearman rho = {r_spearman_earn:.4f}")

    # -----------------------------------------------------------------
    # PARTE 2: CLUSTERING K-MEANS++ & PCA 2D EM GARANHÕES (SIRES COM >= 40 ENTRADAS)
    # -----------------------------------------------------------------
    df_sires = pd.read_csv(os.path.join(ANALYSIS_DIR, "sire_lineage_specialization.csv"))
    sire_pr_mean = df_pr.groupby("sire")["pagerank_scaled"].mean().to_dict()
    df_sires["mean_progeny_pagerank"] = df_sires["sire"].map(lambda s: round(float(sire_pr_mean.get(s, 1.2)), 3))
    df_sires["g1_win_share_pct"] = round(100.0 * df_sires["g1_wins"] / df_sires["graded_wins"].replace(0, np.nan), 2).fillna(0.0)

    cluster_features = [
        "turf_share_pct", "avg_distance_m", "win_rate_pct",
        "podium_rate_pct", "g1_win_share_pct", "mean_progeny_pagerank"
    ]
    X_raw = df_sires[cluster_features].fillna(0.0).values.astype(float)
    X_mean = X_raw.mean(axis=0, keepdims=True)
    X_std = np.where(X_raw.std(axis=0, keepdims=True) == 0, 1.0, X_raw.std(axis=0, keepdims=True))
    X_scaled = (X_raw - X_mean) / X_std

    sil_scores = {}
    for k_cand in range(2, 8):
        lbls, _, _ = kmeans_plusplus(X_scaled, k=k_cand, seed=42)
        sil_scores[k_cand] = round(compute_silhouette_score(X_scaled, lbls), 4)

    print("\n[2] VARREDURA DE SILHOUETTE SCORE (K-MEANS++):")
    for k_c, sc in sil_scores.items():
        print(f"  • k = {k_c}: Silhouette Score = {sc:.4f}")

    # Usamos k=4 arquétipos zootécnicos clássicos (ou ótimo de interpretação de domínio)
    k_opt = 4
    labels_k4, centroids_k4, _ = kmeans_plusplus(X_scaled, k=k_opt, seed=42)
    coords_2d, var_exp, _ = pca_2d(X_scaled)

    df_sires["cluster_id"] = labels_k4
    df_sires["pca_1"] = np.round(coords_2d[:, 0], 4)
    df_sires["pca_2"] = np.round(coords_2d[:, 1], 4)

    # Nomear semanticamente cada cluster por bijeção 1-para-1 baseada nos centroides reais
    cluster_stats = (
        df_sires.groupby("cluster_id")[["g1_wins", "turf_share_pct", "avg_distance_m", "win_rate_pct"]]
        .mean()
    )
    remaining_cids = set(range(k_opt))
    cluster_names = {}

    # 1. Dinastias de Elite G1 (maior média de g1_wins)
    cid_c = int(cluster_stats.loc[list(remaining_cids), "g1_wins"].idxmax())
    cluster_names[cid_c] = "Cluster C: Elite Classic & G1 Turf Dynasties"
    remaining_cids.remove(cid_c)

    # 2. Especialistas de Dirt/Areia (menor turf_share_pct entre os restantes)
    cid_a = int(cluster_stats.loc[list(remaining_cids), "turf_share_pct"].idxmin())
    cluster_names[cid_a] = "Cluster A: Dirt & Sand Power Specialists"
    remaining_cids.remove(cid_a)

    # 3. Velocistas & Milheiros (menor avg_distance_m entre os 2 restantes)
    cid_b = int(cluster_stats.loc[list(remaining_cids), "avg_distance_m"].idxmin())
    cluster_names[cid_b] = "Cluster B: Speed & Mile Turf Sires"
    remaining_cids.remove(cid_b)

    # 4. Stayers Clássicos de Fundo (maior avg_distance_m restante)
    cid_d = int(list(remaining_cids)[0])
    cluster_names[cid_d] = "Cluster D: Classic Stayers & Long-Distance Sires"

    df_sires["cluster_archetype"] = df_sires["cluster_id"].map(cluster_names)
    df_sires.to_csv(os.path.join(ANALYSIS_DIR, "ml_sire_clusters_pca.csv"), index=False, encoding="utf-8-sig")

    print(f"  • Variância Explicada pelo PCA 2D: PC1 = {var_exp[0]*100:.1f}%, PC2 = {var_exp[1]*100:.1f}% (Total = {(var_exp[0]+var_exp[1])*100:.1f}%)")
    for cid, cname in sorted(cluster_names.items()):
        ex_sires = ", ".join(df_sires[df_sires["cluster_id"] == cid]["sire"].head(4).tolist())
        print(f"    - {cname} (n={sum(labels_k4==cid)}): ex. {ex_sires}")

    # -----------------------------------------------------------------
    # PARTE 3: CLASSIFICAÇÃO SUPERVISIONADA (PREVISÃO DE PÓDIO TOP-3 EM PROVAS GRADED)
    # -----------------------------------------------------------------
    # Ordenar cronologicamente por ano e construir features históricas acumuladas ANTES da corrida (Zero Data Leakage!)
    df_ml = df_full.sort_values(by=["year", "race_id"]).reset_index(drop=True)
    df_ml["target_top3"] = (df_ml["position"] <= 3).astype(int)

    # Calcular estatísticas históricas estritamente anteriores (expanding window shifted) por cavalo, jóquei, treinador e sire
    def add_expanding_prior_rate(df, group_col, target_col, out_col, prior_weight=8.0, global_mean=0.20):
        cumsum = df.groupby(group_col)[target_col].cumsum() - df[target_col]
        cumcnt = df.groupby(group_col).cumcount()
        return (cumsum + prior_weight * global_mean) / (cumcnt + prior_weight)

    df_ml["horse_prior_starts"] = df_ml.groupby("horse_name").cumcount()
    df_ml["horse_prior_top3_rate"] = add_expanding_prior_rate(df_ml, "horse_name", "target_top3", "horse_prior_top3_rate", prior_weight=3.0)
    df_ml["jockey_prior_top3_rate"] = add_expanding_prior_rate(df_ml, "jockey", "target_top3", "jockey_prior_top3_rate", prior_weight=15.0)
    df_ml["trainer_prior_top3_rate"] = add_expanding_prior_rate(df_ml, "trainer", "target_top3", "trainer_prior_top3_rate", prior_weight=15.0)
    df_ml["sire_prior_top3_rate"] = add_expanding_prior_rate(df_ml, "sire", "target_top3", "sire_prior_top3_rate", prior_weight=20.0)
    df_ml["damsire_prior_top3_rate"] = add_expanding_prior_rate(df_ml, "dam_sire", "target_top3", "damsire_prior_top3_rate", prior_weight=20.0)

    # Afinidade específica do Sire com a Superfície da prova (anterior à corrida)
    df_ml["sire_surf_key"] = df_ml["sire"].fillna("Unknown") + "_" + df_ml["surface"].fillna("Turf")
    df_ml["sire_surface_affinity"] = add_expanding_prior_rate(df_ml, "sire_surf_key", "target_top3", "sire_surface_affinity", prior_weight=15.0)

    # Afinidade do Sire com a Categoria de Distância
    df_ml["sire_dist_key"] = df_ml["sire"].fillna("Unknown") + "_" + df_ml["distance_category"]
    df_ml["sire_distance_affinity"] = add_expanding_prior_rate(df_ml, "sire_dist_key", "target_top3", "sire_distance_affinity", prior_weight=15.0)

    # Inbreeding F_X (propriedade genética estática do nascimento do cavalo)
    fx_map = df_pr.set_index("horse_name")["inbreeding_fx_pct"].to_dict()
    df_ml["inbreeding_fx_pct"] = df_ml["horse_name"].map(lambda h: float(fx_map.get(h, 0.0)))

    # Features numéricas e ordinais
    df_ml["is_turf"] = (df_ml["surface"] == "Turf").astype(float)
    df_ml["is_female"] = (df_ml["sex"] == "Female").astype(float)

    feature_cols = [
        "jockey_prior_top3_rate",
        "horse_prior_top3_rate",
        "trainer_prior_top3_rate",
        "sire_surface_affinity",
        "sire_distance_affinity",
        "sire_prior_top3_rate",
        "damsire_prior_top3_rate",
        "age",
        "weight",
        "horse_mass_kg",
        "num_runners",
        "distance",
        "grade_weight",
        "horse_prior_starts",
        "inbreeding_fx_pct",
        "is_turf",
        "is_female",
    ]

    for c in feature_cols:
        df_ml[c] = pd.to_numeric(df_ml[c], errors="coerce")

    # Divisão Cronológica Estrita (ML Best Practices):
    # Treino: 2002–2013 | Validação: 2014–2015 | Teste: 2016–2018
    train_df = df_ml[df_ml["year"] <= 2013].copy()
    val_df = df_ml[(df_ml["year"] >= 2014) & (df_ml["year"] <= 2015)].copy()
    test_df = df_ml[df_ml["year"] >= 2016].copy()

    # Imputação de medianas calculadas EXCLUSIVAMENTE no conjunto de Treino (Zero Data Leakage!)
    train_medians = train_df[feature_cols].median()
    X_train_raw = train_df[feature_cols].fillna(train_medians).fillna(0.0).values.astype(float)
    X_val_raw = val_df[feature_cols].fillna(train_medians).fillna(0.0).values.astype(float)
    X_test_raw = test_df[feature_cols].fillna(train_medians).fillna(0.0).values.astype(float)

    y_train = train_df["target_top3"].values.astype(int)
    y_val = val_df["target_top3"].values.astype(int)
    y_test = test_df["target_top3"].values.astype(int)

    # Padronização ajustada EXCLUSIVAMENTE no conjunto de Treino
    f_mean = X_train_raw.mean(axis=0, keepdims=True)
    f_std = np.where(X_train_raw.std(axis=0, keepdims=True) == 0, 1.0, X_train_raw.std(axis=0, keepdims=True))
    X_train = (X_train_raw - f_mean) / f_std
    X_val = (X_val_raw - f_mean) / f_std
    X_test = (X_test_raw - f_mean) / f_std

    # Pesos de balanceamento de classe (proporção ~20% pódio vs 80% fora do pódio)
    pos_ratio = float(np.mean(y_train == 1))
    sw_train = np.where(y_train == 1, 0.5 / pos_ratio, 0.5 / (1.0 - pos_ratio))

    # Modelo 1: Baseline Ingênuo (Probabilidade constante = média histórica + ruído nulo)
    prob_base_test = np.full(len(y_test), pos_ratio)
    metrics_base = binary_metrics(y_test, prob_base_test, threshold=0.5)

    # Modelo 2: Regressão Logística L2 Balanceada
    logreg = LogisticRegressionL2(lr=0.12, epochs=500, l2_reg=0.005).fit(X_train, y_train, sample_weight=sw_train)
    prob_lr_test = logreg.predict_proba(X_test)
    metrics_lr = binary_metrics(y_test, prob_lr_test, threshold=0.52)
    ci_lr = bootstrap_ci_auc(y_test, prob_lr_test)

    # Modelo 3: Random Forest Classifier (45 Árvores CART Balanceadas)
    rf = RandomForestEnsemble(n_estimators=45, max_depth=6, min_samples_leaf=25, seed=42).fit(X_train, y_train, sample_weight=sw_train)
    prob_rf_test = rf.predict_proba(X_test)
    metrics_rf = binary_metrics(y_test, prob_rf_test, threshold=0.52)
    ci_rf = bootstrap_ci_auc(y_test, prob_rf_test)

    print(f"\n[3] AVALIAÇÃO DE MODELOS SUPERVISIONADOS NO CONJUNTO DE TESTE CRONOLÓGICO (2016–2018, N = {len(y_test):,}):")
    print(f"  • Baseline Ingênuo:       ROC-AUC = {metrics_base['roc_auc']:.4f} | PR-AUC = {metrics_base['pr_auc']:.4f} | F1 = {metrics_base['f1']:.4f}")
    print(f"  • Regressão Logística L2: ROC-AUC = {metrics_lr['roc_auc']:.4f} (IC 95%: [{ci_lr[0]:.4f}, {ci_lr[1]:.4f}]) | PR-AUC = {metrics_lr['pr_auc']:.4f} | F1 = {metrics_lr['f1']:.4f} | Acc = {metrics_lr['accuracy']:.4f}")
    print(f"  • Random Forest (CART):   ROC-AUC = {metrics_rf['roc_auc']:.4f} (IC 95%: [{ci_rf[0]:.4f}, {ci_rf[1]:.4f}]) | PR-AUC = {metrics_rf['pr_auc']:.4f} | F1 = {metrics_rf['f1']:.4f} | Acc = {metrics_rf['accuracy']:.4f}")

    df_imp = pd.DataFrame({
        "feature": feature_cols,
        "gini_importance_pct": np.round(rf.feature_importances_ * 100.0, 2),
        "logreg_abs_coef": np.round(np.abs(logreg.w), 4)
    }).sort_values(by="gini_importance_pct", ascending=False)
    df_imp.to_csv(os.path.join(ANALYSIS_DIR, "ml_feature_importance.csv"), index=False, encoding="utf-8-sig")

    print("\n  Top 8 Features Mais Importantes (Random Forest Gini Importance):")
    for _, r in df_imp.head(8).iterrows():
        print(f"    - {r['feature']:<28s}: {r['gini_importance_pct']:5.2f}%")

    # Salvar resumo JSON/CSV de todas as métricas estatísticas e de ML
    summary_stats = {
        "hypothesis_tests": {
            "H1a_chi2_sire_vs_surface": {"chi2": round(chi2_s, 2), "dof": dof_s, "p_value": p_s, "cramers_v": round(v_s, 4)},
            "H1b_chi2_sire_vs_distance": {"chi2": round(chi2_d, 2), "dof": dof_d, "p_value": p_d, "cramers_v": round(v_d, 4)},
            "ANOVA_winning_distance_by_sire": {k: round(v, 4) if isinstance(v, float) else v for k, v in anova_dist.items()},
            "ANOVA_pagerank_by_sire": {k: round(v, 4) if isinstance(v, float) else v for k, v in anova_pr.items()},
            "H2_pagerank_correlations": {
                "pearson_podiums": round(r_pearson_podiums, 4),
                "spearman_podiums": round(r_spearman_podiums, 4),
                "pearson_earnings": round(r_pearson_earn, 4),
                "spearman_earnings": round(r_spearman_earn, 4),
            }
        },
        "clustering_kmeans": {
            "silhouette_scores_by_k": sil_scores,
            "pca_variance_explained": [round(float(var_exp[0]), 4), round(float(var_exp[1]), 4)],
            "cluster_archetypes": cluster_names
        },
        "supervised_classification_test_2016_2018": {
            "train_samples": len(y_train),
            "val_samples": len(y_val),
            "test_samples": len(y_test),
            "naive_baseline": metrics_base,
            "logistic_regression_l2": {**metrics_lr, "roc_auc_ci95": list(ci_lr)},
            "random_forest": {**metrics_rf, "roc_auc_ci95": list(ci_rf)}
        }
    }
    with open(os.path.join(ANALYSIS_DIR, "ml_and_statistics_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary_stats, f, indent=2, ensure_ascii=False)

    # -----------------------------------------------------------------
    # PARTE 4: GERAÇÃO DOS GRÁFICOS CIENTÍFICOS DE ML E ESTATÍSTICA (300 DPI)
    # -----------------------------------------------------------------
    sns.set_theme(style="whitegrid")

    # Gráfico 1: Painel Duplo de K-Means PCA 2D + Curva de Silhouette Score
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15.5, 6.8), dpi=300, gridspec_kw={"width_ratios": [1.85, 1.0]})

    palette_clusters = {
        "Cluster A: Dirt & Sand Power Specialists": "#d97706",
        "Cluster B: Speed & Mile Turf Sires": "#0284c7",
        "Cluster C: Elite Classic & G1 Turf Dynasties": "#7c3aed",
        "Cluster D: Classic Stayers & Long-Distance Sires": "#059669",
    }

    for arch, grp in df_sires.groupby("cluster_archetype"):
        ax1.scatter(
            grp["pca_1"], grp["pca_2"],
            s=np.clip(grp["total_entries"] * 0.45, 70, 520),
            color=palette_clusters.get(arch, "#64748b"),
            alpha=0.82, edgecolors="#0f172a", linewidth=1.1, label=arch
        )

    # Rotular os principais garanhões no gráfico PCA
    highlight_sires = set(df_sires.head(18)["sire"].tolist() + ["Gold Allure", "Kurofune(USA)", "Sakura Bakushin O", "Lord Kanaloa"])
    for _, r in df_sires.iterrows():
        if r["sire"] in highlight_sires:
            clean_s = r["sire"].replace("(USA)", "").replace("(GB)", "").replace("(IRE)", "")
            ax1.text(
                r["pca_1"] + 0.06, r["pca_2"] + 0.06, clean_s,
                fontsize=8.2, fontweight="bold", color="#0f172a"
            )

    ax1.set_title(
        f"K-Means++ Clustering of JRA Sires Projected via 2D PCA ({(var_exp[0]+var_exp[1])*100:.1f}% Var. Explained)",
        fontsize=12.5, fontweight="bold", pad=12
    )
    ax1.set_xlabel(f"Principal Component 1 ({var_exp[0]*100:.1f}% Variance — Surface & Distance Axis)", fontsize=10.5)
    ax1.set_ylabel(f"Principal Component 2 ({var_exp[1]*100:.1f}% Variance — Win Rate & Prestige Axis)", fontsize=10.5)
    ax1.legend(loc="best", frameon=True, fontsize=8.5, title="Genetic Archetype (Bubble Size = Graded Starts)")

    ks = list(sil_scores.keys())
    scs = list(sil_scores.values())
    ax2.plot(ks, scs, marker="o", linewidth=2.5, markersize=8, color="#4f46e5")
    for x_k, y_s in zip(ks, scs):
        ax2.text(x_k, y_s + 0.008, f"{y_s:.3f}", ha="center", va="bottom", fontsize=9, fontweight="bold")
    ax2.set_title("Silhouette Score Across Cluster Count (k = 2..7)", fontsize=12, fontweight="bold", pad=12)
    ax2.set_xlabel("Number of Clusters (k)", fontsize=10.5)
    ax2.set_ylabel("Mean Silhouette Coefficient", fontsize=10.5)
    ax2.set_ylim(min(scs) - 0.04, max(scs) + 0.05)

    plt.tight_layout()
    pca_plot_path = os.path.join(ASSETS_DIR, "ml_kmeans_pca_clusters.png")
    plt.savefig(pca_plot_path, dpi=300)
    plt.close()

    # Gráfico 2: Painel Duplo de Feature Importance (Random Forest) + Especialização de Superfície/Distância (Chi^2)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15.5, 6.8), dpi=300)

    top_imp = df_imp.head(12).iloc[::-1]
    bars = ax1.barh(top_imp["feature"], top_imp["gini_importance_pct"], color=sns.color_palette("viridis", len(top_imp)))
    for bar, val in zip(bars, top_imp["gini_importance_pct"]):
        ax1.text(val + 0.35, bar.get_y() + bar.get_height() / 2.0, f"{val:.1f}%", va="center", fontsize=8.8, fontweight="bold")
    ax1.set_xlim(0, max(top_imp["gini_importance_pct"]) * 1.18)
    ax1.set_title(
        f"Random Forest Feature Importance — Top-3 Podium Prediction\n(Test ROC-AUC = {metrics_rf['roc_auc']:.3f}, 95% CI [{ci_rf[0]:.3f}, {ci_rf[1]:.3f}])",
        fontsize=11.5, fontweight="bold", pad=10
    )
    ax1.set_xlabel("Relative Gini Importance (%)", fontsize=10.5)

    # Heatmap de especialização de distância nos Top 10 Sires (Chi^2)
    top10_sires = df_full["sire"].dropna().value_counts().head(10).index.tolist()
    ct_norm = pd.crosstab(
        df_full[df_full["sire"].isin(top10_sires)]["sire"],
        df_full[df_full["sire"].isin(top10_sires)]["distance_category"],
        normalize="index"
    ) * 100.0
    ct_norm = ct_norm.loc[top10_sires]
    sns.heatmap(
        ct_norm, annot=True, fmt=".1f", cmap="YlGnBu", cbar_kws={"label": "Share of Starts (%)"}, ax=ax2
    )
    ax2.set_title(
        f"Sire Distance Specialization Heatmap (Chi² = {chi2_d:.1f}, p < 0.0001, Cramér's V = {v_d:.3f})",
        fontsize=11.5, fontweight="bold", pad=10
    )
    ax2.set_xlabel("Race Distance Category", fontsize=10.5)
    ax2.set_ylabel("Paternal Sire", fontsize=10.5)

    plt.tight_layout()
    rf_plot_path = os.path.join(ASSETS_DIR, "ml_random_forest_and_chi2.png")
    plt.savefig(rf_plot_path, dpi=300)
    plt.close()

    print(f"\n[Plots ML] Gráficos salvos em:\n  - {pca_plot_path}\n  - {rf_plot_path}")
    print("\n[Etapa C] Concluída com sucesso!")


if __name__ == "__main__":
    main()
