"""Consortium management package for Xcapit Privacy Platform.

This package provides modular management of data collaboration
consortiums between multiple companies.

The ConsortiumManager class serves as a facade that provides
backward compatibility with the original monolithic implementation.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import (
    Company,
    Consortium,
    ConsortiumStatus,
    DataContribution,
    Invitation,
    InviteStatus,
    Membership,
    MemberRole,
    MemberStatus,
)
from .database import DatabaseManager
from .core import CoreManager
from .governance import GovernanceManager
from .compliance import ComplianceManager
from .data_quality import DataQualityManager
from .marketplace import MarketplaceManager
from .sandbox import SandboxManager
from .federated import FederatedManager
from .explainability import ExplainabilityManager
from .competitive_insights import CompetitiveInsightsManager
from .ensemble import EnsembleManager


class ConsortiumManager:
    """Unified manager for all consortium operations.

    This class serves as a facade that delegates to specialized managers
    while maintaining backward compatibility with the original API.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize consortium manager.

        Args:
            db_path: Path to SQLite database.
        """
        self.db_path = db_path or Path("./data/fheml.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize specialized managers
        self._db = DatabaseManager(self.db_path)
        self._core = CoreManager(self.db_path)
        self._governance = GovernanceManager(self.db_path)
        self._compliance = ComplianceManager(self.db_path)
        self._data_quality = DataQualityManager(self.db_path, core_manager=self._core)
        self._marketplace = MarketplaceManager(self.db_path)
        self._sandbox = SandboxManager(self.db_path)
        self._federated = FederatedManager(self.db_path)
        self._explainability = ExplainabilityManager(self.db_path, core_manager=self._core)
        self._competitive = CompetitiveInsightsManager(self.db_path)
        self._ensemble = EnsembleManager(self.db_path)

        # Initialize core schema
        self._db.init_core_schema()

    # ========== Database Connection (for backward compatibility) ==========

    def _get_connection(self):
        """Get database connection (for backward compatibility)."""
        return self._db.get_connection()

    def _init_schema(self):
        """Initialize core schema (for backward compatibility)."""
        self._db.init_core_schema()

    # ========== Company Operations (delegated to CoreManager) ==========

    def create_company(self, name: str, email: str, api_key: Optional[str] = None,
                       metadata: Optional[Dict] = None) -> tuple[Company, str]:
        return self._core.create_company(name, email, api_key, metadata)

    def get_company_by_api_key(self, api_key: str) -> Optional[Company]:
        return self._core.get_company_by_api_key(api_key)

    def get_company(self, company_id: str) -> Optional[Company]:
        return self._core.get_company(company_id)

    # ========== Consortium Operations (delegated to CoreManager) ==========

    def create_consortium(self, name: str, description: Optional[str] = None,
                          owner_id: Optional[str] = None, model_type: str = "linear_regression",
                          model_config: Optional[Dict] = None, metadata: Optional[Dict] = None,
                          created_by: Optional[str] = None) -> Consortium:
        return self._core.create_consortium(name, description, owner_id, model_type,
                                            model_config, metadata, created_by)

    def get_consortium(self, consortium_id: str) -> Optional[Consortium]:
        return self._core.get_consortium(consortium_id)

    def _row_to_consortium(self, row) -> Consortium:
        return self._core._row_to_consortium(row)

    def list_consortiums(self, company_id: Optional[str] = None,
                         status: Optional[ConsortiumStatus] = None) -> List[Consortium]:
        return self._core.list_consortiums(company_id, status)

    def update_consortium_status(self, consortium_id: str,
                                 status: ConsortiumStatus) -> Optional[Consortium]:
        return self._core.update_consortium_status(consortium_id, status)

    # ========== Membership Operations (delegated to CoreManager) ==========

    def get_members(self, consortium_id: str) -> List[Dict]:
        return self._core.get_members(consortium_id)

    def get_membership(self, consortium_id: str, company_id: str) -> Optional[Membership]:
        return self._core.get_membership(consortium_id, company_id)

    # ========== Invitation Operations (delegated to CoreManager) ==========

    def create_invitation(self, consortium_id: str, invited_by: str, invite_email: str,
                          role: MemberRole = MemberRole.CONTRIBUTOR,
                          expires_in_days: int = 7) -> Invitation:
        return self._core.create_invitation(consortium_id, invited_by, invite_email,
                                            role, expires_in_days)

    def get_invitation_by_code(self, invite_code: str) -> Optional[Invitation]:
        return self._core.get_invitation_by_code(invite_code)

    def accept_invitation(self, invite_code: str, company_id: str) -> Optional[Membership]:
        return self._core.accept_invitation(invite_code, company_id)

    def list_invitations(self, consortium_id: str,
                         status: Optional[InviteStatus] = None) -> List[Invitation]:
        return self._core.list_invitations(consortium_id, status)

    # ========== Data Contribution Operations (delegated to CoreManager) ==========

    def record_data_contribution(self, consortium_id: str, company_id: str,
                                 encrypted_blob_path: str, record_count: int,
                                 feature_count: int, checksum: str,
                                 metadata: Optional[Dict] = None) -> DataContribution:
        return self._core.record_data_contribution(consortium_id, company_id,
                                                   encrypted_blob_path, record_count,
                                                   feature_count, checksum, metadata)

    def get_consortium_data_summary(self, consortium_id: str) -> Dict:
        return self._core.get_consortium_data_summary(consortium_id)

    def get_data_contributions(self, consortium_id: str) -> List[DataContribution]:
        return self._core.get_data_contributions(consortium_id)

    def add_data_contribution(self, consortium_id: str, company_id: str,
                              contribution_id: str, record_count: int, file_path: str,
                              feature_count: int = 0, metadata: Dict = None) -> DataContribution:
        return self._core.add_data_contribution(consortium_id, company_id, contribution_id,
                                                record_count, file_path, feature_count, metadata)

    def update_member_data_status(self, consortium_id: str, company_id: str,
                                  data_uploaded: bool, record_count: int) -> None:
        return self._core.update_member_data_status(consortium_id, company_id,
                                                    data_uploaded, record_count)

    def get_consortium_stats(self, consortium_id: str) -> Dict[str, Any]:
        return self._core.get_consortium_stats(consortium_id)

    # ========== Governance Operations (delegated to GovernanceManager) ==========

    def _init_governance_schema(self):
        """Initialize governance schema (for backward compatibility)."""
        self._db.init_governance_schema()

    def record_contribution_proof(self, consortium_id: str, company_id: str,
                                  record_count: int, feature_count: int,
                                  data_hash: str, checksum: str) -> str:
        return self._governance.record_contribution_proof(consortium_id, company_id,
                                                          record_count, feature_count,
                                                          data_hash, checksum)

    def get_contribution_proofs(self, consortium_id: str) -> List[Dict]:
        return self._governance.get_contribution_proofs(consortium_id)

    def get_contribution_summary(self, consortium_id: str) -> List[Dict]:
        return self._governance.get_contribution_summary(consortium_id)

    def get_member_contribution_summary(self, consortium_id: str, company_id: str) -> Dict:
        return self._governance.get_member_contribution_summary(consortium_id, company_id)

    def create_proposal(self, consortium_id: str, proposer_id: str, proposal_type: str,
                        title: str, description: str = "", data: Optional[Dict] = None,
                        voting_duration: int = 86400) -> str:
        return self._governance.create_proposal(consortium_id, proposer_id, proposal_type,
                                                title, description, data, voting_duration)

    def get_proposal(self, proposal_id: str) -> Optional[Dict]:
        return self._governance.get_proposal(proposal_id)

    def get_proposals(self, consortium_id: str, status_filter: Optional[str] = None) -> List[Dict]:
        return self._governance.get_proposals(consortium_id, status_filter)

    def record_vote(self, proposal_id: str, voter_id: str, support: bool,
                    weight: int, comment: Optional[str] = None) -> str:
        return self._governance.record_vote(proposal_id, voter_id, support, weight, comment)

    def get_vote(self, proposal_id: str, voter_id: str) -> Optional[Dict]:
        return self._governance.get_vote(proposal_id, voter_id)

    def get_proposal_votes(self, proposal_id: str) -> List[Dict]:
        return self._governance.get_proposal_votes(proposal_id)

    def execute_proposal(self, proposal_id: str) -> Dict:
        return self._governance.execute_proposal(proposal_id)

    def record_audit_event(self, consortium_id: str, event_type: str, actor_id: str,
                           target_id: Optional[str] = None, target_type: Optional[str] = None,
                           data: Optional[Dict] = None) -> str:
        return self._governance.record_audit_event(consortium_id, event_type, actor_id,
                                                   target_id, target_type, data)

    def get_audit_trail(self, consortium_id: str, event_type: Optional[str] = None,
                        limit: int = 100, offset: int = 0) -> List[Dict]:
        return self._governance.get_audit_trail(consortium_id, event_type, limit, offset)

    def verify_audit_trail(self, consortium_id: str) -> bool:
        return self._governance.verify_audit_trail(consortium_id)

    def calculate_reward_distribution(self, consortium_id: str, total_amount: float) -> List[Dict]:
        return self._governance.calculate_reward_distribution(consortium_id, total_amount)

    def record_reward_distribution(self, consortium_id: str, total_amount: float,
                                   distributions: List[Dict]) -> str:
        return self._governance.record_reward_distribution(consortium_id, total_amount, distributions)

    def get_reward_distributions(self, consortium_id: str) -> List[Dict]:
        return self._governance.get_reward_distributions(consortium_id)

    # Schema initialization methods (for backward compatibility)
    def _init_compliance_schema(self):
        self._db.init_compliance_schema()

    def _init_data_quality_schema(self):
        self._db.init_data_quality_schema()

    def _init_marketplace_schema(self):
        self._db.init_marketplace_schema()

    def _init_sandbox_schema(self):
        self._db.init_sandbox_schema()

    def _init_federated_schema(self):
        self._db.init_federated_schema()

    def _init_explainability_schema(self):
        self._db.init_explainability_schema()

    def _init_competitive_insights_schema(self):
        self._db.init_competitive_insights_schema()

    def _init_ensemble_schema(self):
        self._db.init_ensemble_schema()

    # ========== Compliance Operations (TIER 3) - Delegated to ComplianceManager ==========

    def get_compliance_frameworks(self) -> List[Dict]:
        return self._compliance.get_compliance_frameworks()

    def get_compliance_framework(self, framework_id: str) -> Optional[Dict]:
        return self._compliance.get_compliance_framework(framework_id)

    def enable_compliance_framework(self, consortium_id: str, framework_id: str,
                                    settings: Optional[Dict] = None) -> Dict:
        return self._compliance.enable_compliance_framework(consortium_id, framework_id)

    def record_compliance_check(self, consortium_id: str, framework_id: str,
                                control_id: str, status: str, result: Optional[str] = None,
                                evidence: Optional[Dict] = None, checked_by: Optional[str] = None,
                                notes: Optional[str] = None) -> str:
        return self._compliance.record_compliance_check(consortium_id, framework_id, control_id,
                                                        status, result, evidence, checked_by, notes)

    def get_compliance_checks(self, consortium_id: str, framework_id: Optional[str] = None,
                              status: Optional[str] = None) -> List[Dict]:
        return self._compliance.get_compliance_checks(consortium_id, framework_id, status)

    def generate_compliance_report(self, consortium_id: str, framework_id: str) -> Dict:
        return self._compliance.generate_compliance_report(consortium_id, framework_id)

    def get_compliance_reports(self, consortium_id: str, framework_id: Optional[str] = None) -> List[Dict]:
        return self._compliance.get_compliance_reports(consortium_id, framework_id)

    def create_attestation(self, consortium_id: str, framework_id: str,
                           attested_by: str, statement: str,
                           control_id: Optional[str] = None, attester_role: Optional[str] = None,
                           attestation_type: str = "manual",
                           evidence_urls: Optional[List[str]] = None,
                           valid_days: int = 365) -> str:
        return self._compliance.create_attestation(consortium_id, framework_id, attested_by,
                                                   statement, control_id, attester_role,
                                                   attestation_type, evidence_urls, valid_days)

    def get_attestations(self, consortium_id: str, framework_id: Optional[str] = None,
                         include_revoked: bool = False) -> List[Dict]:
        return self._compliance.get_attestations(consortium_id, framework_id, include_revoked)

    def record_data_processing(self, consortium_id: str, company_id: str,
                               processing_purpose: str, data_categories: List[str],
                               legal_basis: str, **kwargs) -> str:
        return self._compliance.record_data_processing(consortium_id, company_id, processing_purpose,
                                                       data_categories, legal_basis, **kwargs)

    def get_data_processing_records(self, consortium_id: str, company_id: Optional[str] = None) -> List[Dict]:
        return self._compliance.get_data_processing_records(consortium_id, company_id)

    def get_consortium_compliance_settings(self, consortium_id: str) -> Dict:
        return self._compliance.get_consortium_compliance_settings(consortium_id)

    def get_compliance_dashboard(self, consortium_id: str) -> Dict:
        return self._compliance.get_compliance_dashboard(consortium_id)

    # ========== Data Quality Operations (TIER 3) - Delegated to DataQualityManager ==========

    def assess_data_quality(self, consortium_id: str, company_id: str, **kwargs) -> Dict:
        return self._data_quality.assess_data_quality(consortium_id, company_id, **kwargs)

    def get_quality_assessments(self, consortium_id: str, company_id: Optional[str] = None,
                                limit: int = 100) -> List[Dict]:
        return self._data_quality.get_quality_assessments(consortium_id, company_id, limit)

    def get_latest_quality_assessment(self, consortium_id: str, company_id: str) -> Optional[Dict]:
        return self._data_quality.get_latest_quality_assessment(consortium_id, company_id)

    def get_quality_history(self, consortium_id: str, company_id: Optional[str] = None,
                            metric_type: Optional[str] = None, days: int = 30) -> List[Dict]:
        return self._data_quality.get_quality_history(consortium_id, company_id, metric_type, days)

    def set_quality_rule(self, consortium_id: str, rule_name: str, rule_type: str,
                         threshold_min: Optional[float] = None,
                         threshold_max: Optional[float] = None,
                         weight: float = 1.0) -> str:
        return self._data_quality.set_quality_rule(consortium_id, rule_name, rule_type,
                                                   threshold_min, threshold_max, weight)

    def get_quality_rules(self, consortium_id: str) -> List[Dict]:
        return self._data_quality.get_quality_rules(consortium_id)

    def get_quality_alerts(self, consortium_id: str, company_id: Optional[str] = None,
                           severity: Optional[str] = None,
                           acknowledged: Optional[bool] = None, limit: int = 100) -> List[Dict]:
        return self._data_quality.get_quality_alerts(consortium_id, company_id, severity, acknowledged, limit)

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        return self._data_quality.acknowledge_alert(alert_id, acknowledged_by)

    def get_consortium_quality_dashboard(self, consortium_id: str) -> Dict:
        return self._data_quality.get_consortium_quality_dashboard(consortium_id)

    # ========== Marketplace Operations (TIER 3) - Delegated to MarketplaceManager ==========

    def get_marketplace_categories(self) -> List[Dict]:
        return self._marketplace.get_marketplace_categories()

    def get_marketplace_models(self, industry: Optional[str] = None,
                               model_type: Optional[str] = None,
                               featured_only: bool = False,
                               search: Optional[str] = None,
                               sort_by: str = "downloads",
                               limit: int = 50) -> List[Dict]:
        return self._marketplace.get_marketplace_models(industry, model_type, featured_only,
                                                        search, sort_by, limit)

    def get_marketplace_model(self, model_id: str) -> Optional[Dict]:
        return self._marketplace.get_marketplace_model(model_id)

    def deploy_marketplace_model(self, model_id: str, consortium_id: str,
                                 deployed_by: str, config: Optional[Dict] = None) -> Dict:
        return self._marketplace.deploy_marketplace_model(model_id, consortium_id, deployed_by, config)

    def get_consortium_deployments(self, consortium_id: str) -> List[Dict]:
        return self._marketplace.get_consortium_deployments(consortium_id)

    def undeploy_model(self, deployment_id: str, undeployed_by: Optional[str] = None) -> bool:
        return self._marketplace.undeploy_model(deployment_id, undeployed_by)

    def add_model_review(self, model_id: str, reviewer_id: str, rating: int,
                         title: Optional[str] = None, comment: Optional[str] = None,
                         consortium_id: Optional[str] = None) -> str:
        return self._marketplace.add_model_review(model_id, reviewer_id, rating, title, comment, consortium_id)

    def get_model_reviews(self, model_id: str, limit: int = 50) -> List[Dict]:
        return self._marketplace.get_model_reviews(model_id, limit)

    def get_featured_models(self, limit: int = 6) -> List[Dict]:
        return self._marketplace.get_featured_models(limit)

    def get_marketplace_stats(self) -> Dict:
        return self._marketplace.get_marketplace_stats()

    # ========== Sandbox Operations (TIER 3) - Delegated to SandboxManager ==========

    def create_sandbox(self, name: str, owner_id: str, description: Optional[str] = None,
                       template_id: Optional[str] = None, industry: Optional[str] = None,
                       expires_days: int = 7) -> Dict:
        return self._sandbox.create_sandbox(name, owner_id, description, template_id,
                                            industry, expires_days)

    def get_sandbox(self, sandbox_id: str) -> Optional[Dict]:
        return self._sandbox.get_sandbox(sandbox_id)

    def list_sandboxes(self, owner_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict]:
        return self._sandbox.list_sandboxes(owner_id, status)

    def delete_sandbox(self, sandbox_id: str, owner_id: Optional[str] = None) -> bool:
        return self._sandbox.delete_sandbox(sandbox_id, owner_id)

    def generate_synthetic_dataset(self, sandbox_id: str, name: str, dataset_type: str,
                                   created_by: str, record_count: int = 1000,
                                   description: Optional[str] = None,
                                   config: Optional[Dict] = None) -> Dict:
        return self._sandbox.generate_synthetic_dataset(sandbox_id, name, dataset_type,
                                                        created_by, record_count, description, config)

    def get_dataset(self, dataset_id: str) -> Optional[Dict]:
        return self._sandbox.get_dataset(dataset_id)

    def list_datasets(self, sandbox_id: str) -> List[Dict]:
        return self._sandbox.list_datasets(sandbox_id)

    def delete_dataset(self, dataset_id: str, owner_id: Optional[str] = None) -> bool:
        return self._sandbox.delete_dataset(dataset_id, owner_id)

    def create_experiment(self, sandbox_id: str, name: str, experiment_type: str,
                          created_by: str, model_type: Optional[str] = None,
                          dataset_id: Optional[str] = None, description: Optional[str] = None,
                          config: Optional[Dict] = None) -> Dict:
        return self._sandbox.create_experiment(sandbox_id, name, experiment_type, created_by,
                                               model_type, dataset_id, description, config)

    def get_experiment(self, experiment_id: str) -> Optional[Dict]:
        return self._sandbox.get_experiment(experiment_id)

    def list_experiments(self, sandbox_id: str) -> List[Dict]:
        return self._sandbox.list_experiments(sandbox_id)

    def run_experiment(self, experiment_id: str) -> Dict:
        return self._sandbox.run_experiment(experiment_id)

    def delete_experiment(self, experiment_id: str, owner_id: Optional[str] = None) -> bool:
        return self._sandbox.delete_experiment(experiment_id, owner_id)

    def list_sandbox_templates(self, industry: Optional[str] = None) -> List[Dict]:
        return self._sandbox.list_sandbox_templates(industry)

    def get_sandbox_stats(self, owner_id: Optional[str] = None) -> Dict:
        return self._sandbox.get_sandbox_stats(owner_id)

    # ========== Federated Learning Operations (TIER 4) - Delegated to FederatedManager ==========

    def create_inference_endpoint(self, consortium_id: str, company_id: str,
                                  name: str, **kwargs) -> Dict:
        return self._federated.create_inference_endpoint(consortium_id, company_id, name, **kwargs)

    def get_inference_endpoint(self, endpoint_id: str) -> Optional[Dict]:
        return self._federated.get_inference_endpoint(endpoint_id)

    def list_inference_endpoints(self, consortium_id: Optional[str] = None,
                                 company_id: Optional[str] = None,
                                 status: Optional[str] = None) -> List[Dict]:
        return self._federated.list_inference_endpoints(consortium_id, company_id, status)

    def delete_inference_endpoint(self, endpoint_id: str, company_id: Optional[str] = None) -> bool:
        return self._federated.delete_inference_endpoint(endpoint_id, company_id)

    def submit_inference_request(self, endpoint_id: str, requester_id: str,
                                 input_data: Any, **kwargs) -> Dict:
        return self._federated.submit_inference_request(endpoint_id, requester_id, input_data, **kwargs)

    def get_inference_request(self, request_id: str) -> Optional[Dict]:
        return self._federated.get_inference_request(request_id)

    def list_inference_requests(self, endpoint_id: Optional[str] = None,
                                requester_id: Optional[str] = None,
                                status: Optional[str] = None) -> List[Dict]:
        return self._federated.list_inference_requests(endpoint_id, requester_id, status)

    def get_inference_result(self, request_id: str) -> Optional[Dict]:
        return self._federated.get_inference_result(request_id)

    def create_federated_model(self, consortium_id: str, name: str,
                               model_type: str, **kwargs) -> Dict:
        return self._federated.create_federated_model(consortium_id, name, model_type, **kwargs)

    def get_federated_model(self, model_id: str) -> Optional[Dict]:
        return self._federated.get_federated_model(model_id)

    def list_federated_models(self, consortium_id: Optional[str] = None,
                              status: Optional[str] = None) -> List[Dict]:
        return self._federated.list_federated_models(consortium_id, status=status)

    def register_edge_node(self, company_id: str, name: str, **kwargs) -> Dict:
        return self._federated.register_edge_node(company_id, name, **kwargs)

    def get_edge_node(self, node_id: str) -> Optional[Dict]:
        return self._federated.get_edge_node(node_id)

    def list_edge_nodes(self, company_id: Optional[str] = None) -> List[Dict]:
        return self._federated.list_edge_nodes(company_id)

    def deploy_model_to_edge(self, node_id: str, model_id: str,
                             company_id: Optional[str] = None) -> Dict:
        return self._federated.deploy_model_to_edge(node_id, model_id, company_id)

    def update_edge_heartbeat(self, node_id: str) -> bool:
        return self._federated.update_edge_heartbeat(node_id)

    def delete_edge_node(self, node_id: str, company_id: Optional[str] = None) -> bool:
        return self._federated.delete_edge_node(node_id, company_id)

    def get_federated_stats(self, company_id: Optional[str] = None,
                            consortium_id: Optional[str] = None) -> Dict:
        return self._federated.get_federated_stats(company_id)

    # ========== Explainability Operations (TIER 4) - Delegated to ExplainabilityManager ==========

    def request_explanation(self, consortium_id: str, requester_id: str,
                            explanation_type: str, **kwargs) -> Dict:
        return self._explainability.request_explanation(consortium_id, requester_id, explanation_type, **kwargs)

    def get_explanation(self, request_id: str) -> Optional[Dict]:
        return self._explainability.get_explanation(request_id)

    def list_explanations(self, consortium_id: str, requester_id: Optional[str] = None,
                          explanation_type: Optional[str] = None, limit: int = 50) -> List[Dict]:
        return self._explainability.list_explanations(consortium_id, requester_id, explanation_type, limit)

    def get_feature_importance(self, consortium_id: str, model_id: Optional[str] = None) -> List[Dict]:
        return self._explainability.get_feature_importance(consortium_id, model_id)

    def compute_model_insights(self, consortium_id: str, model_id: Optional[str] = None) -> Dict:
        return self._explainability.compute_model_insights(consortium_id, model_id)

    def get_explainability_stats(self, consortium_id: Optional[str] = None) -> Dict:
        return self._explainability.get_explainability_stats(consortium_id)

    # ========== Competitive Insights Operations (TIER 4) - Delegated to CompetitiveInsightsManager ==========

    def get_industry_benchmarks(self, industry: str, metric_type: Optional[str] = None) -> List[Dict]:
        return self._competitive.get_industry_benchmarks(industry, metric_type)

    def compare_to_industry(self, company_id: str, industry: str,
                            metrics: Optional[Dict[str, float]] = None) -> Dict:
        return self._competitive.compare_to_industry(company_id, industry, metrics)

    def get_industry_trends(self, industry: str, period: str = "quarterly") -> List[Dict]:
        return self._competitive.get_industry_trends(industry, period)

    def get_competitive_position(self, company_id: str, consortium_id: Optional[str] = None) -> Dict:
        return self._competitive.get_competitive_position(company_id, consortium_id)

    def get_competitive_insights_stats(self) -> Dict:
        return self._competitive.get_competitive_insights_stats()

    # ========== Ensemble Operations (TIER 4) - Delegated to EnsembleManager ==========

    def create_ensemble(self, name: str, description: str, owner_id: str,
                        ensemble_type: str = "voting") -> Dict:
        return self._ensemble.create_ensemble(name, description, owner_id, ensemble_type)

    def add_model_to_ensemble(self, ensemble_id: str, model_id: str,
                              consortium_id: str, model_type: str,
                              weight: float = 1.0) -> Dict:
        return self._ensemble.add_model_to_ensemble(ensemble_id, model_id, consortium_id, model_type, weight)

    def get_ensemble(self, ensemble_id: str) -> Optional[Dict]:
        return self._ensemble.get_ensemble(ensemble_id)

    def list_ensembles(self, owner_id: Optional[str] = None, status: Optional[str] = None,
                       limit: int = 50) -> List[Dict]:
        return self._ensemble.list_ensembles(owner_id, status, limit)

    def activate_ensemble(self, ensemble_id: str, requester_id: str) -> Dict:
        return self._ensemble.activate_ensemble(ensemble_id, requester_id)

    def predict_with_ensemble(self, ensemble_id: str, requester_id: str,
                              input_data: Any) -> Dict:
        return self._ensemble.predict_with_ensemble(ensemble_id, requester_id, input_data)

    def get_ensemble_performance(self, ensemble_id: str) -> Dict:
        return self._ensemble.get_ensemble_performance(ensemble_id)

    def get_ensemble_stats(self, owner_id: Optional[str] = None) -> Dict:
        return self._ensemble.get_ensemble_stats(owner_id)


# Public exports
__all__ = [
    # Models
    "Company",
    "Consortium",
    "ConsortiumStatus",
    "DataContribution",
    "Invitation",
    "InviteStatus",
    "Membership",
    "MemberRole",
    "MemberStatus",
    # Managers
    "ConsortiumManager",
    "CoreManager",
    "GovernanceManager",
    "ComplianceManager",
    "DataQualityManager",
    "MarketplaceManager",
    "SandboxManager",
    "FederatedManager",
    "ExplainabilityManager",
    "CompetitiveInsightsManager",
    "EnsembleManager",
    "DatabaseManager",
]
