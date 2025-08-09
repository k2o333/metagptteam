#!/usr/bin/env python3
# mghier/scripts/test_hierarchical_integration.py

import asyncio
import sys
from pathlib import Path
import yaml

# Add the root of the MetaGPT project to the Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from metagpt.config2 import Config
from hierarchical.context import HierarchicalContext
from metagpt.llm import LLM
from metagpt.team import Team
from hierarchical.roles import ChiefPM, Scheduler, Executor, Archiver
from hierarchical.roles.change_coordinator import ChangeCoordinator
from hierarchical.roles.section_applier import SectionApplier
from hierarchical.actions.research import Research
from hierarchical.actions.research_reviewer import ResearchReviewer
from hierarchical.actions.document_adaptation_planner import DocumentAdaptationPlanner
from hierarchical.actions.section_rewriter import SectionRewriter

async def test_role_initialization():
    """测试所有角色的正确初始化"""
    print("Testing role initialization...")
    
    # Initialize LLM and Context
    llm = LLM()
    ctx = HierarchicalContext(llm=llm)
    
    # Load configuration
    global_config_path = Path("/root/.metagpt/config2.yaml")
    local_config_path = PROJECT_ROOT / "configs" / "local_config.yaml"
    
    global_config = Config.from_yaml_file(global_config_path)
    raw_global_config_data = yaml.safe_load(global_config_path.read_text()) or {}
    local_config_data = yaml.safe_load(local_config_path.read_text()) or {}
    merged_config_data = {**raw_global_config_data, **local_config_data}
    
    # Set custom configuration in context
    ctx.kwargs.custom_config = merged_config_data
    ctx.kwargs.strategy_config = local_config_data
    
    # Initialize Research Actions
    research_action = Research(context=ctx)
    research_reviewer_action = ResearchReviewer(context=ctx)
    document_adaptation_planner_action = DocumentAdaptationPlanner(context=ctx)
    section_rewriter_action = SectionRewriter(context=ctx)
    
    # Test role initialization
    try:
        chief_pm = ChiefPM(context=ctx)
        scheduler = Scheduler(context=ctx)
        executor = Executor(context=ctx)
        archiver = Archiver(context=ctx)
        
        coordinator = ChangeCoordinator(
            context=ctx,
            research_action=research_action,
            research_reviewer_action=research_reviewer_action,
            document_adaptation_planner_action=document_adaptation_planner_action,
            section_rewriter_action=section_rewriter_action
        )
        applier = SectionApplier(context=ctx)
        
        print("✓ All roles initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Role initialization failed: {e}")
        return False

async def test_team_assembly():
    """测试团队组建"""
    print("Testing team assembly...")
    
    # Initialize LLM and Context
    llm = LLM()
    ctx = HierarchicalContext(llm=llm)
    
    # Load configuration
    global_config_path = Path("/root/.metagpt/config2.yaml")
    local_config_path = PROJECT_ROOT / "configs" / "local_config.yaml"
    
    global_config = Config.from_yaml_file(global_config_path)
    raw_global_config_data = yaml.safe_load(global_config_path.read_text()) or {}
    local_config_data = yaml.safe_load(local_config_path.read_text()) or {}
    merged_config_data = {**raw_global_config_data, **local_config_data}
    
    # Set custom configuration in context
    ctx.kwargs.custom_config = merged_config_data
    ctx.kwargs.strategy_config = local_config_data
    
    # Initialize Research Actions
    research_action = Research(context=ctx)
    research_reviewer_action = ResearchReviewer(context=ctx)
    document_adaptation_planner_action = DocumentAdaptationPlanner(context=ctx)
    section_rewriter_action = SectionRewriter(context=ctx)
    
    try:
        # Create team with complete role system
        team = Team(context=ctx, use_mgx=False)
        chief_pm = ChiefPM(context=ctx)
        scheduler = Scheduler(context=ctx)
        executor = Executor(context=ctx)
        archiver = Archiver(context=ctx)
        
        coordinator = ChangeCoordinator(
            context=ctx,
            research_action=research_action,
            research_reviewer_action=research_reviewer_action,
            document_adaptation_planner_action=document_adaptation_planner_action,
            section_rewriter_action=section_rewriter_action
        )
        applier = SectionApplier(context=ctx)
        
        # Hire all roles
        team.hire([chief_pm, scheduler, executor, archiver, coordinator, applier])
        
        # Check if all roles are hired
        hired_roles = list(team.env.roles.keys())
        expected_roles = ["ChiefPM", "Scheduler", "Executor", "Archiver", "ChangeCoordinator", "SectionApplier"]
        
        if set(hired_roles) == set(expected_roles):
            print("✓ Team assembled with all roles successfully")
            return True
        else:
            print(f"✗ Team assembly incomplete. Expected: {expected_roles}, Got: {hired_roles}")
            return False
    except Exception as e:
        print(f"✗ Team assembly failed: {e}")
        return False

async def test_enhanced_mode_config():
    """测试增强模式配置"""
    print("Testing enhanced mode configuration...")
    
    # Load configuration
    local_config_path = PROJECT_ROOT / "configs" / "local_config.yaml"
    local_config_data = yaml.safe_load(local_config_path.read_text()) or {}
    
    # Check if hierarchical_doc_adapter section exists
    if "hierarchical_doc_adapter" in local_config_data:
        enhanced_mode = local_config_data["hierarchical_doc_adapter"].get("enhanced_mode", False)
        print(f"✓ Enhanced mode configuration found. Current setting: {enhanced_mode}")
        return True
    else:
        print("✗ Enhanced mode configuration not found")
        return False

async def main():
    """主测试函数"""
    print("=== Hierarchical Integration Test ===\n")
    
    tests = [
        test_role_initialization,
        test_team_assembly,
        test_enhanced_mode_config
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
            print()
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}\n")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("=== Test Summary ===")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)