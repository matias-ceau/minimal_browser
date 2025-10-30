# Investigation Documentation Index

This directory contains a comprehensive investigation into limiting factors and potential Tauri engine integration for the minimal_browser project.

## 📚 Documentation Structure

### 1. Entry Points

#### 🎯 **Start Here:** [QUICK_REFERENCE.md](./QUICK_REFERENCE.md)
**Best for:** Quick overview, comparison table, recommendation summary  
**Read time:** 3-5 minutes  
**Content:** At-a-glance comparison, decision summary, phased roadmap, success metrics

#### 📋 **Executive Summary:** [INVESTIGATION_SUMMARY.md](./INVESTIGATION_SUMMARY.md)  
**Best for:** Team leads, decision makers  
**Read time:** 10-15 minutes  
**Content:** Key findings, recommendations, decision tree, next actions

### 2. Comprehensive Analysis

#### 📖 **Full Investigation:** [INVESTIGATION_TAURI_ENGINE.md](./INVESTIGATION_TAURI_ENGINE.md)
**Best for:** Technical deep-dive, architectural decisions  
**Read time:** 45-60 minutes  
**Content:** 
- Current architecture analysis (stack, dependencies, bottlenecks)
- Detailed Tauri overview and capabilities
- Comparative analysis with decision framework
- Integration feasibility (full migration vs hybrid vs incremental)
- 4-phase optimization roadmap with timelines
- Risk assessment and mitigation strategies
- POC specification for hybrid approach
- Code examples (PyO3, Tauri IPC)
- Performance profiling specifications

**Sections:**
1. Current Architecture Analysis
2. Identified Limiting Factors
3. Tauri Overview and Capabilities
4. Comparative Analysis
5. Integration Feasibility Analysis
6. Recommendations and Next Steps
7. Risk Assessment
8. Decision Framework
9. Proof of Concept Specification
10. Conclusion
11. Appendices (References, Code Examples, Profiling)

### 3. Tools

#### 🔧 **Performance Profiling:** [scripts/profile_performance.py](./scripts/profile_performance.py)
**Purpose:** Measure current performance baselines  
**Usage:**
```bash
# Profile startup time
python scripts/profile_performance.py --startup

# Profile HTML rendering
python scripts/profile_performance.py --html-rendering

# Profile memory usage
python scripts/profile_performance.py --memory

# Run all tests
python scripts/profile_performance.py --all
```

## 🎯 Key Recommendation

**Do NOT pursue full Tauri migration.** Follow incremental optimization path:

1. **Phase 1 (Weeks 1-2):** Profile & optimize Qt → 20-30% improvements
2. **Phase 2 (Weeks 3-6):** Add PyO3 extensions for hotspots → 30-50% improvements
3. **Phase 3 (Months 3-4):** Better packaging → 50% size reduction
4. **Phase 4 (Months 6+):** Evaluate hybrid Tauri only if needed

## 📊 Quick Comparison

| Metric | Current | Target (Phase 3) | Tauri (Full Migration) |
|--------|---------|------------------|------------------------|
| Binary Size | 300MB | 200MB | 5-15MB |
| Startup Time | 2-3s | 1-1.5s | <500ms |
| Memory Usage | 150-200MB | 120-150MB | 50-100MB |
| Migration Cost | - | 4-6 weeks | 8-12 weeks |
| Risk Level | Low | Low-Medium | High |
| Python Integration | ✅ Native | ✅ Native | ❌ Complex |

## 🔗 Related Documentation

- **Architecture:** [ARCHITECTURE.md](../development/ARCHITECTURE.md)
- **Feature Requests:** [FEATURE_REQUESTS.md](FEATURE_REQUESTS.md) (see FR-060)
- **Roadmap:** [ROADMAP.md](ROADMAP.md)
- **Contributing:** [CONTRIBUTING.md](../development/CONTRIBUTING.md)

## 📅 Investigation Timeline

- **Investigation Date:** 2025-01-09
- **Related Issues:** [FR-003: Native Module Optimization](https://github.com/matias-ceau/minimal_browser/issues/3), FR-060
- **Status:** Complete - Recommendations provided

## 🚀 Next Steps

**This Week:**
1. ✅ Review investigation documents
2. ⏳ Run baseline profiling
3. ⏳ Discuss Phase 1 priorities with team

**Weeks 1-2:** Implement Phase 1 optimizations  
**Week 3:** Review results, decide on Phase 2

## 💡 Key Insights

> **Bottom Line:** Current Qt WebEngine architecture is well-suited for minimal_browser's Python-heavy AI integration. Focus on incremental optimizations rather than risky full migration. The existing engine abstraction layer provides flexibility for future experiments without committing to major rewrites.

---

*For questions or discussion, please comment on issue [FR-003](https://github.com/matias-ceau/minimal_browser/issues/3)*
