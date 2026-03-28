from sqlalchemy.orm import Session
from backend.recommendations.models import Recommendation, RecommendationCategory, RecommendationRiskLevel
from backend.financial_profile.models import RiskProfile, GoalType
from backend.logger import get_logger

logger = get_logger(__name__)

# Rule-based recommendation templates
RULES: list[dict] = [
    {
        "risk_profiles": [RiskProfile.conservative],
        "goal_types": [GoalType.retirement],
        "category": RecommendationCategory.pension,
        "title": "III. pilier — Doplnkové dôchodkové sporenie (DDS)",
        "description": (
            "Odporúčame otvoriť III. pilier u niektorého z DDS fondov (napr. NN, Uniqa, Kooperativa). "
            "Štát prispieva až €180/rok pri vklade min. €25/mes. Ideálne pre konzervatívnych sporiteľov."
        ),
        "expected_return": 3.5,
        "risk_level": RecommendationRiskLevel.low,
    },
    {
        "risk_profiles": [RiskProfile.conservative],
        "goal_types": [GoalType.retirement, GoalType.savings],
        "category": RecommendationCategory.investment,
        "title": "Štátne dlhopisy SR",
        "description": (
            "Slovenské štátne dlhopisy ponúkajú garantovaný výnos a nízke riziko. "
            "Vhodné ako základ konzervatívneho portfólia."
        ),
        "expected_return": 4.0,
        "risk_level": RecommendationRiskLevel.low,
    },
    {
        "risk_profiles": [RiskProfile.balanced],
        "goal_types": [GoalType.retirement, GoalType.growth],
        "category": RecommendationCategory.investment,
        "title": "ETF MSCI World — globálne akcie",
        "description": (
            "Diverzifikovaný ETF fond sledujúci globálny akciový index. "
            "Odporúčaný horizont 5+ rokov. Dostupný cez brokerov ako Degiro alebo XTB."
        ),
        "expected_return": 8.0,
        "risk_level": RecommendationRiskLevel.medium,
    },
    {
        "risk_profiles": [RiskProfile.balanced],
        "goal_types": [GoalType.retirement],
        "category": RecommendationCategory.pension,
        "title": "II. pilier — optimalizácia fondu",
        "description": (
            "Prehodnoťte aktuálny fond v II. pilieri. Pre vek pod 40 odporúčame indexový fond "
            "(napr. Finax, NN Growth). Pre vek nad 50 odporúčame prechod na konzervatívny fond."
        ),
        "expected_return": 6.0,
        "risk_level": RecommendationRiskLevel.medium,
    },
    {
        "risk_profiles": [RiskProfile.aggressive],
        "goal_types": [GoalType.growth],
        "category": RecommendationCategory.investment,
        "title": "Individuálne akcie — rastové spoločnosti",
        "description": (
            "Pre agresívnych investorov odporúčame alokáciu časti portfólia do individuálnych akcií "
            "(tech sektor, EV, AI). Odporúčaný broker: Interactive Brokers."
        ),
        "expected_return": 15.0,
        "risk_level": RecommendationRiskLevel.high,
    },
    {
        "risk_profiles": [RiskProfile.aggressive],
        "goal_types": [GoalType.growth],
        "category": RecommendationCategory.investment,
        "title": "ETF malých spoločností (Small Cap ETF)",
        "description": (
            "Small Cap ETF (napr. iShares MSCI World Small Cap) historicky prekonáva large cap "
            "na dlhom horizonte, avšak s vyššou volatilitou."
        ),
        "expected_return": 11.0,
        "risk_level": RecommendationRiskLevel.high,
    },
    # Universal rules (any risk profile)
    {
        "risk_profiles": list(RiskProfile),
        "goal_types": [GoalType.property],
        "category": RecommendationCategory.credit,
        "title": "Porovnanie hypoték na slovenskom trhu",
        "description": (
            "Odporúčame porovnať ponuky hypoték v Tatra banka, ČSOB, Slovenská sporiteľňa a VÚB. "
            "Aktuálne sadzby: 3.5–4.5% p.a. Žiadosť cez finančného sprostredkovateľa je zadarmo."
        ),
        "expected_return": None,
        "risk_level": RecommendationRiskLevel.low,
    },
    {
        "risk_profiles": list(RiskProfile),
        "goal_types": [GoalType.property],
        "category": RecommendationCategory.investment,
        "title": "Stavebné sporenie",
        "description": (
            "Stavebné sporenie (napr. Prvá stavebná sporiteľňa) ponúka garantovaný výnos + štátnu prémiu "
            "až €66.39/rok. Vhodné ako príprava na hypotéku."
        ),
        "expected_return": 2.5,
        "risk_level": RecommendationRiskLevel.low,
    },
    {
        "risk_profiles": list(RiskProfile),
        "goal_types": [GoalType.savings],
        "category": RecommendationCategory.investment,
        "title": "Termínovaný vklad",
        "description": (
            "Termínovaný vklad v banke (12 mes.) so sadzbou 3.0–4.0% p.a. Bez rizika, poistené FPDP."
        ),
        "expected_return": 3.5,
        "risk_level": RecommendationRiskLevel.low,
    },
    {
        "risk_profiles": list(RiskProfile),
        "goal_types": [GoalType.savings],
        "category": RecommendationCategory.investment,
        "title": "Money Market ETF",
        "description": (
            "Likvidný Money Market ETF (napr. iShares € Govt Bond 0-1yr) ako alternatíva k bežnému účtu. "
            "Výnos cca 3.5% p.a. s dennou likviditou."
        ),
        "expected_return": 3.5,
        "risk_level": RecommendationRiskLevel.low,
    },
]


def generate_recommendations(db: Session, user_id: int, risk_profile: RiskProfile, goal_type: GoalType) -> list[Recommendation]:
    # Remove old recommendations for this user
    db.query(Recommendation).filter(Recommendation.user_id == user_id).delete()

    results = []
    seen_titles: set[str] = set()

    for rule in RULES:
        if risk_profile in rule["risk_profiles"] and goal_type in rule["goal_types"]:
            if rule["title"] in seen_titles:
                continue
            seen_titles.add(rule["title"])
            rec = Recommendation(
                user_id=user_id,
                category=rule["category"],
                title=rule["title"],
                description=rule["description"],
                expected_return=rule["expected_return"],
                risk_level=rule["risk_level"],
            )
            db.add(rec)
            results.append(rec)

    db.commit()
    for r in results:
        db.refresh(r)
    logger.info(
        "Generated %d recommendations for user_id=%s (risk=%s, goal=%s)",
        len(results), user_id, risk_profile.value, goal_type.value,
    )
    return results


def get_recommendations(db: Session, user_id: int) -> list[Recommendation]:
    return db.query(Recommendation).filter(Recommendation.user_id == user_id).all()
