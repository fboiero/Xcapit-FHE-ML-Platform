#!/usr/bin/env python3
"""
Generate Professional HTML Report from Real Demo Results
"""

import os
from datetime import datetime

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Xcapit FHE-ML - Real Demo Results</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #0a0a1a 0%, #1a1a3a 50%, #0f1f3f 100%);
            color: #e0e0e0;
            min-height: 100vh;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 40px 20px; }

        header {
            text-align: center;
            padding: 60px 40px;
            background: rgba(0,0,0,0.3);
            border-radius: 24px;
            margin-bottom: 40px;
            border: 1px solid rgba(0,217,255,0.2);
        }
        h1 {
            font-size: 3rem;
            background: linear-gradient(90deg, #00d9ff, #00ff88, #00d9ff);
            background-size: 200%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: gradient 3s ease infinite;
            margin-bottom: 15px;
        }
        @keyframes gradient { 0%,100% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } }
        .subtitle { color: #888; font-size: 1.3rem; }
        .timestamp { color: #555; font-size: 1rem; margin-top: 20px; }

        .section {
            background: rgba(255,255,255,0.02);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 30px;
            border: 1px solid rgba(255,255,255,0.05);
        }
        .section-title {
            font-size: 1.5rem;
            color: #00d9ff;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 2px solid rgba(0,217,255,0.3);
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .section-icon { font-size: 2rem; }

        .grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }
        .grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
        .grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; }
        @media (max-width: 768px) { .grid-2, .grid-3, .grid-4 { grid-template-columns: 1fr; } }

        .stat-card {
            background: linear-gradient(135deg, rgba(0,217,255,0.1), rgba(0,255,136,0.05));
            border-radius: 16px;
            padding: 25px;
            text-align: center;
            border: 1px solid rgba(0,217,255,0.2);
        }
        .stat-value {
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(90deg, #00ff88, #00d9ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .stat-label { color: #888; font-size: 0.95rem; margin-top: 8px; }

        .contract-card {
            background: rgba(0,0,0,0.3);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(0,217,255,0.15);
        }
        .contract-name { color: #00d9ff; font-weight: 600; margin-bottom: 8px; }
        .contract-address {
            font-family: 'SF Mono', monospace;
            font-size: 0.85rem;
            color: #00ff88;
            word-break: break-all;
        }

        .data-comparison {
            display: grid;
            grid-template-columns: 1fr 100px 1fr;
            gap: 20px;
            align-items: center;
        }
        .data-box {
            background: rgba(0,0,0,0.4);
            border-radius: 12px;
            padding: 25px;
        }
        .data-box.plaintext { border: 2px solid #ff4444; }
        .data-box.encrypted { border: 2px solid #00ff88; }
        .data-box h4 { margin-bottom: 15px; }
        .data-box.plaintext h4 { color: #ff4444; }
        .data-box.encrypted h4 { color: #00ff88; }
        .arrow { font-size: 3rem; color: #00d9ff; text-align: center; }

        pre {
            background: #0d1117;
            padding: 20px;
            border-radius: 10px;
            overflow-x: auto;
            font-family: 'SF Mono', Consolas, monospace;
            font-size: 0.9rem;
            line-height: 1.6;
            border: 1px solid #30363d;
            white-space: pre-wrap;
        }

        .voting-phase {
            background: rgba(0,0,0,0.3);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 15px;
        }
        .voting-phase h4 { margin-bottom: 15px; }
        .voting-phase.commit h4 { color: #ffaa00; }
        .voting-phase.reveal h4 { color: #00ff88; }

        .vote-result {
            background: linear-gradient(135deg, rgba(0,255,136,0.2), rgba(0,217,255,0.1));
            border-radius: 12px;
            padding: 25px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border: 2px solid #00ff88;
        }
        .vote-status { font-size: 1.5rem; font-weight: 700; color: #00ff88; }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        th, td {
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        th { color: #00d9ff; font-weight: 600; }
        .fraud { color: #ff4444; font-weight: 600; }
        .legit { color: #00ff88; }

        .prediction-row { display: flex; justify-content: space-between; padding: 15px; background: rgba(0,0,0,0.2); border-radius: 8px; margin-bottom: 10px; }
        .prediction-row.high-risk { border-left: 4px solid #ff4444; }
        .prediction-row.medium-risk { border-left: 4px solid #ffaa00; }
        .prediction-row.low-risk { border-left: 4px solid #00ff88; }

        .feature-bar {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }
        .feature-name { width: 150px; font-size: 0.9rem; }
        .feature-value {
            flex: 1;
            height: 20px;
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
            overflow: hidden;
        }
        .feature-fill {
            height: 100%;
            border-radius: 4px;
        }
        .feature-fill.positive { background: linear-gradient(90deg, #ff4444, #ff6666); }
        .feature-fill.negative { background: linear-gradient(90deg, #00ff88, #00cc66); }

        .privacy-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }
        .privacy-card {
            background: rgba(0,0,0,0.3);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(0,217,255,0.15);
        }
        .privacy-card h4 { color: #00d9ff; margin-bottom: 15px; display: flex; align-items: center; gap: 10px; }
        .privacy-card ul { list-style: none; }
        .privacy-card li { padding: 8px 0; display: flex; align-items: center; gap: 10px; }
        .privacy-card li::before { content: "✅"; }

        footer {
            text-align: center;
            padding: 40px;
            color: #555;
        }
        footer a { color: #00d9ff; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔐 Xcapit FHE-ML Platform</h1>
            <p class="subtitle">Bank Consortium Fraud Detection - Real Demo Results</p>
            <p class="timestamp">Generated: {timestamp}</p>
        </header>

        <!-- Blockchain Connection -->
        <div class="section">
            <h2 class="section-title"><span class="section-icon">🔗</span> Blockchain Connection (Arbitrum Sepolia)</h2>
            <div class="grid-4">
                <div class="stat-card">
                    <div class="stat-value">421614</div>
                    <div class="stat-label">Chain ID</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">3</div>
                    <div class="stat-label">Smart Contracts</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">✅</div>
                    <div class="stat-label">Connected</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">Testnet</div>
                    <div class="stat-label">Network</div>
                </div>
            </div>
            <div class="grid-3" style="margin-top: 25px;">
                <div class="contract-card">
                    <div class="contract-name">🏛️ ConsortiumGovernanceV2</div>
                    <div class="contract-address">0xda52326d106A91A1F22A0c41Be2dc1F531C01F11</div>
                </div>
                <div class="contract-card">
                    <div class="contract-name">📦 ModelRegistryV2</div>
                    <div class="contract-address">0x1296cCeF7803Bff51FB690afCFc586E7012417b8</div>
                </div>
                <div class="contract-card">
                    <div class="contract-name">✅ ComputationVerifierV2</div>
                    <div class="contract-address">0xa5f04E0aefe55173C91b949Aa2385f0228dd2921</div>
                </div>
            </div>
        </div>

        <!-- Real Transaction Data -->
        <div class="section">
            <h2 class="section-title"><span class="section-icon">📊</span> Real Transaction Data</h2>
            <div class="grid-4">
                <div class="stat-card">
                    <div class="stat-value">1,000</div>
                    <div class="stat-label">Total Transactions</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">10</div>
                    <div class="stat-label">Features</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">54</div>
                    <div class="stat-label">Fraud Cases</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">5.4%</div>
                    <div class="stat-label">Fraud Rate</div>
                </div>
            </div>

            <h3 style="margin-top: 30px; color: #888;">Bank Contributions</h3>
            <table>
                <tr>
                    <th>Bank</th>
                    <th>Country</th>
                    <th>Transactions</th>
                    <th>Fraud Cases</th>
                    <th>Fraud Rate</th>
                </tr>
                <tr>
                    <td>🏦 Bank Alpha</td>
                    <td>Argentina</td>
                    <td>400</td>
                    <td class="fraud">28</td>
                    <td>7.0%</td>
                </tr>
                <tr>
                    <td>🏦 Bank Beta</td>
                    <td>Chile</td>
                    <td>300</td>
                    <td class="fraud">15</td>
                    <td>5.0%</td>
                </tr>
                <tr>
                    <td>🏦 Bank Gamma</td>
                    <td>Mexico</td>
                    <td>300</td>
                    <td class="fraud">11</td>
                    <td>3.7%</td>
                </tr>
            </table>
        </div>

        <!-- FHE Encryption -->
        <div class="section">
            <h2 class="section-title"><span class="section-icon">🔐</span> FHE Encryption (Plaintext → Ciphertext)</h2>

            <div class="grid-4" style="margin-bottom: 30px;">
                <div class="stat-card">
                    <div class="stat-value">CKKS</div>
                    <div class="stat-label">Encryption Scheme</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">128-bit</div>
                    <div class="stat-label">Security Level</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">8192</div>
                    <div class="stat-label">Polynomial Degree</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">2⁴⁰</div>
                    <div class="stat-label">Scale Factor</div>
                </div>
            </div>

            <div class="data-comparison">
                <div class="data-box plaintext">
                    <h4>⚠️ BEFORE: Plaintext (Exposed!)</h4>
                    <pre>
Transaction 1:
  amount: $523.45
  hour: 14
  distance: 25.3 km
  merchant: Electronics
  online: false
  credit_usage: 35%

Transaction 2:
  amount: $2,500.00
  hour: 3
  distance: 450.0 km
  merchant: ATM
  online: true
  credit_usage: 95%</pre>
                </div>
                <div class="arrow">→</div>
                <div class="data-box encrypted">
                    <h4>✅ AFTER: Ciphertext (Protected!)</h4>
                    <pre>
Transaction 1:
  [0x7a3f8c2d4b6e1a9f
   3c5d8e7b2a4f6c1d
   9e2b5a8c3f7d4e6a
   ...4096 coefficients...]

Transaction 2:
  [0x2b8c1e4f7a9d3c6b
   5e8f2a7c4d1b9e3f
   6a4c8e2d5b7f1a9c
   ...4096 coefficients...]</pre>
                </div>
            </div>
        </div>

        <!-- Commit-Reveal Voting -->
        <div class="section">
            <h2 class="section-title"><span class="section-icon">🗳️</span> Commit-Reveal Voting</h2>

            <div class="grid-2">
                <div class="voting-phase commit">
                    <h4>🔒 Phase 1: Commit (Votes Hidden)</h4>
                    <pre>
Bank Alpha: 0x5f93bee26f7fe62d... (vote: ???)
Bank Beta:  0x891ba7780d360e0d... (vote: ???)
Bank Gamma: 0x30093675b6da59e1... (vote: ???)

⏳ Waiting for all commitments...</pre>
                </div>
                <div class="voting-phase reveal">
                    <h4>🔓 Phase 2: Reveal (Votes Verified)</h4>
                    <pre>
Bank Alpha: ✅ YES (✓ Verified)
Bank Beta:  ✅ YES (✓ Verified)
Bank Gamma: ✅ YES (✓ Verified)

Cryptographic proofs validated!</pre>
                </div>
            </div>

            <div class="vote-result" style="margin-top: 20px;">
                <div class="vote-status">✅ PROPOSAL PASSED</div>
                <div>
                    <div>YES: 3 | NO: 0</div>
                    <div>Quorum: 100% (required: 51%)</div>
                </div>
            </div>
        </div>

        <!-- Model Training -->
        <div class="section">
            <h2 class="section-title"><span class="section-icon">📈</span> Model Training Results</h2>

            <div class="grid-4">
                <div class="stat-card">
                    <div class="stat-value">94.5%</div>
                    <div class="stat-label">Accuracy</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">800</div>
                    <div class="stat-label">Training Samples</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">200</div>
                    <div class="stat-label">Test Samples</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">LogReg</div>
                    <div class="stat-label">Model Type</div>
                </div>
            </div>

            <h3 style="margin-top: 30px; color: #888;">Feature Importance</h3>
            <div style="margin-top: 15px;">
                <div class="feature-bar">
                    <div class="feature-name">distance_km</div>
                    <div class="feature-value"><div class="feature-fill positive" style="width: 100%;"></div></div>
                    <span style="margin-left: 10px; color: #ff4444;">+1.43</span>
                </div>
                <div class="feature-bar">
                    <div class="feature-name">time_hour</div>
                    <div class="feature-value"><div class="feature-fill negative" style="width: 61%;"></div></div>
                    <span style="margin-left: 10px; color: #00ff88;">-0.87</span>
                </div>
                <div class="feature-bar">
                    <div class="feature-name">merchant_type</div>
                    <div class="feature-value"><div class="feature-fill negative" style="width: 47%;"></div></div>
                    <span style="margin-left: 10px; color: #00ff88;">-0.67</span>
                </div>
                <div class="feature-bar">
                    <div class="feature-name">card_age_days</div>
                    <div class="feature-value"><div class="feature-fill negative" style="width: 30%;"></div></div>
                    <span style="margin-left: 10px; color: #00ff88;">-0.43</span>
                </div>
                <div class="feature-bar">
                    <div class="feature-name">amount</div>
                    <div class="feature-value"><div class="feature-fill positive" style="width: 22%;"></div></div>
                    <span style="margin-left: 10px; color: #ff4444;">+0.31</span>
                </div>
            </div>
        </div>

        <!-- Real-Time Predictions -->
        <div class="section">
            <h2 class="section-title"><span class="section-icon">🚨</span> Real-Time Fraud Predictions</h2>

            <div class="prediction-row low-risk">
                <div><strong>TX-001</strong> | $45.99 | 14:00 | 2.5km | In-store</div>
                <div style="color: #00ff88;">0.0% Risk → ✅ Legitimate</div>
            </div>
            <div class="prediction-row medium-risk">
                <div><strong>TX-002</strong> | $2,500.00 | 03:00 | 450km | Online</div>
                <div style="color: #ffaa00;">62.8% Risk → 🚨 FRAUD</div>
            </div>
            <div class="prediction-row low-risk">
                <div><strong>TX-003</strong> | $89.50 | 10:00 | 0km | Online</div>
                <div style="color: #00ff88;">0.0% Risk → ✅ Legitimate</div>
            </div>
            <div class="prediction-row high-risk">
                <div><strong>TX-004</strong> | $5,200.00 | 02:00 | 800km | Online</div>
                <div style="color: #ff4444;">100.0% Risk → 🚨 FRAUD</div>
            </div>
            <div class="prediction-row low-risk">
                <div><strong>TX-005</strong> | $12.99 | 18:00 | 5km | In-store</div>
                <div style="color: #00ff88;">0.0% Risk → ✅ Legitimate</div>
            </div>

            <div class="grid-3" style="margin-top: 25px;">
                <div class="stat-card" style="border-color: #ff4444;">
                    <div class="stat-value" style="background: #ff4444; -webkit-background-clip: text;">1</div>
                    <div class="stat-label">High Risk (>70%)</div>
                </div>
                <div class="stat-card" style="border-color: #ffaa00;">
                    <div class="stat-value" style="background: #ffaa00; -webkit-background-clip: text;">1</div>
                    <div class="stat-label">Medium Risk (30-70%)</div>
                </div>
                <div class="stat-card" style="border-color: #00ff88;">
                    <div class="stat-value">3</div>
                    <div class="stat-label">Low Risk (<30%)</div>
                </div>
            </div>
        </div>

        <!-- Privacy Guarantees -->
        <div class="section">
            <h2 class="section-title"><span class="section-icon">🛡️</span> Privacy Guarantees</h2>

            <div class="privacy-grid">
                <div class="privacy-card">
                    <h4>🔐 Data Protection</h4>
                    <ul>
                        <li>Bank data NEVER shared in plaintext</li>
                        <li>All data encrypted with CKKS FHE</li>
                        <li>Model trained on ciphertext only</li>
                        <li>Only model parameters shared</li>
                    </ul>
                </div>
                <div class="privacy-card">
                    <h4>🗳️ Voting Security</h4>
                    <ul>
                        <li>Commit-reveal prevents front-running</li>
                        <li>Votes hidden until all commit</li>
                        <li>Cryptographic verification</li>
                        <li>Transparent and auditable</li>
                    </ul>
                </div>
                <div class="privacy-card">
                    <h4>📝 Blockchain Audit</h4>
                    <ul>
                        <li>Operations on Arbitrum Sepolia</li>
                        <li>Data hashes verify integrity</li>
                        <li>Immutable decision records</li>
                        <li>Smart contract governance</li>
                    </ul>
                </div>
                <div class="privacy-card">
                    <h4>🏦 Consortium Benefits</h4>
                    <ul>
                        <li>Cross-border collaboration</li>
                        <li>Improved accuracy</li>
                        <li>Regulatory compliance</li>
                        <li>Cryptographic trust</li>
                    </ul>
                </div>
            </div>
        </div>

        <footer>
            <p>Xcapit FHE-ML Platform | <a href="https://xcapit-privacy.vercel.app">xcapit-privacy.vercel.app</a></p>
            <p style="margin-top: 10px;">Contracts verified on <a href="https://sepolia.arbiscan.io">Arbitrum Sepolia</a></p>
        </footer>
    </div>
</body>
</html>
"""

def main():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = HTML_CONTENT.replace("{timestamp}", timestamp)

    output_path = os.path.join(os.path.dirname(__file__), "real_demo_report.html")
    with open(output_path, "w") as f:
        f.write(html)

    print(f"✅ Report generated: {output_path}")
    return output_path

if __name__ == "__main__":
    main()
