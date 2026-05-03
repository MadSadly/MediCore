import React, { useState, useRef, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { Upload, BarChart, LineChart, PieChart, FlaskConical, BrainCircuit, CheckCircle, XCircle, Loader2 } from 'lucide-react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8080';

const COLOR = {
  primary: '#4da6ff',
  secondary: '#8b949e',
  success: '#34d399',
  danger: '#f87171',
  warning: '#fbbf24',
  bg: '#0d1117',
  panel: '#161b22',
  border: '#21262d',
  text: '#e6edf3',
  dim: '#3d444d',
};

const Card = ({ title, children, icon: Icon, color = COLOR.primary }) => (
  <div style={{ background: COLOR.panel, border: `1px solid ${COLOR.border}`, borderRadius: 8, padding: 20 }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 15 }}>
      {Icon && <Icon size={20} color={color} />}
      <h3 style={{ fontSize: 18, fontWeight: 600, color: COLOR.text, margin: 0 }}>{title}</h3>
    </div>
    {children}
  </div>
);

const Button = ({ onClick, disabled, children, primary = false, icon: Icon }) => (
  <button
    onClick={onClick}
    disabled={disabled}
    style={{
      display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
      padding: '10px 15px', borderRadius: 6, fontSize: 14, fontWeight: 600,
      cursor: disabled ? 'not-allowed' : 'pointer',
      background: primary ? COLOR.primary : COLOR.dim,
      color: COLOR.text,
      border: `1px solid ${primary ? COLOR.primary : COLOR.border}`,
      opacity: disabled ? 0.6 : 1,
      transition: 'all 0.2s',
      '&:hover': {
        background: primary ? '#3a8cdb' : '#5a626b',
      },
    }}
  >
    {Icon && <Icon size={18} />}
    {children}
  </button>
);

const Spinner = ({ size = 20, color = COLOR.primary }) => (
  <Loader2 size={size} color={color} style={{ animation: 'spin 1s linear infinite' }} />
);

export default function ColonCancerPage() {
  const { id: patientId } = useParams();
  const fileInputRef = useRef(null);

  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [dataAnalysisResults, setDataAnalysisResults] = useState(null);
  const [modelTrainingResults, setModelTrainingResults] = useState(null);
  const [inputs, setInputs] = useState({
    age: 65,
    cancerStage: 'Stage III',
    tumorSize: 45.5,
    bmi: 28.2,
    diabetes: 'No'
  });
  const [predictionResult, setPredictionResult] = useState(null);
  const [diagnosisHistory, setDiagnosisHistory] = useState([]);

  useEffect(() => {
    // 진단 기록 불러오기
    const fetchDiagnosisHistory = async () => {
      const token = localStorage.getItem('token');
      if (!token || !patientId) return;
      try {
        const res = await axios.get(`${BACKEND_URL}/api/patients/${patientId}/diagnoses`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setDiagnosisHistory(res.data.filter(d => d.diseaseType === 'colon-cancer'));
      } catch (err) {
        console.error("Failed to fetch diagnosis history:", err);
      }
    };
    fetchDiagnosisHistory();
  }, [patientId]);

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
      setError('');
    }
  };

  const handleDataAnalysis = async () => {
    if (!selectedFile) {
      setError('데이터 파일을 선택해주세요.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      const res = await axios.post(`${BACKEND_URL}/api/gw/colon/data-analysis`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setDataAnalysisResults(res.data);
      alert('데이터 분석 및 전처리 시각화 데이터 생성 완료!');
    } catch (err) {
      setError(err.response?.data?.detail || '데이터 분석 실패');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleModelTraining = async () => {
    if (!selectedFile) {
      setError('데이터 파일을 선택해주세요.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      const res = await axios.post(`${BACKEND_URL}/api/gw/colon/model-training`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setModelTrainingResults(res.data);
      alert('모델 학습, 최적화 및 파이프라인 저장 완료!');
    } catch (err) {
      setError(err.response?.data?.detail || '모델 학습 실패');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handlePrediction = async () => {
    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('token');
      const res = await axios.post(`${BACKEND_URL}/api/gw/colon/predict/${patientId}`, {
        age: inputs.age, cancerStage: inputs.cancerStage, tumorSize: inputs.tumorSize, bmi: inputs.bmi, diabetes: inputs.diabetes
      }, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setPredictionResult(res.data);
      // 예측 후 진단 기록 다시 불러오기
      const updatedHistory = await axios.get(`${BACKEND_URL}/api/patients/${patientId}/diagnoses`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setDiagnosisHistory(updatedHistory.data.filter(d => d.diseaseType === 'colon-cancer'));
      alert('예측 완료 및 진단 기록 저장!');
    } catch (err) {
      setError(err.response?.data?.detail || '예측 실패');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ background: COLOR.bg, color: COLOR.text, minHeight: '100vh', padding: 20, fontFamily: 'system-ui, sans-serif' }}>
      <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 30, color: COLOR.text }}>
        대장암 예측 AI 상담 프로그램 (환자 ID: {patientId})
      </h1>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 20 }}>
        {/* 1. 데이터 업로드 및 분석 */}
        <Card title="데이터 준비 및 분석" icon={Upload}>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            style={{ display: 'none' }}
            accept=".csv"
          />
          <Button onClick={() => fileInputRef.current.click()} disabled={loading} icon={Upload}>
            {selectedFile ? selectedFile.name : 'CSV 파일 선택'}
          </Button>
          <Button onClick={handleDataAnalysis} disabled={loading || !selectedFile} primary icon={BarChart} style={{ marginTop: 10 }}>
            {loading ? <Spinner /> : '데이터 분석 및 전처리'}
          </Button>
          {error && <p style={{ color: COLOR.danger, marginTop: 10 }}>{error}</p>}
          {dataAnalysisResults && (
            <div style={{ marginTop: 20, borderTop: `1px solid ${COLOR.border}`, paddingTop: 20 }}>
              <h4 style={{ color: COLOR.primary, marginBottom: 10 }}>분석 결과 요약:</h4>
              <pre style={{ background: COLOR.dim, padding: 10, borderRadius: 4, fontSize: 12, overflowX: 'auto' }}>
                {JSON.stringify(dataAnalysisResults.eda_results, null, 2)}
              </pre>
              {/* TODO: dataAnalysisResults.preprocessing_visualization_data를 사용하여 차트 그리기 */}
              <p style={{ color: COLOR.secondary, fontSize: 12, marginTop: 10 }}>
                (EDA 및 전처리 시각화 데이터는 콘솔 또는 별도 컴포넌트에서 확인)
              </p>
            </div>
          )}
        </Card>

        {/* 2. 모델 학습 및 최적화 */}
        <Card title="모델 학습 및 최적화" icon={FlaskConical}>
          <Button onClick={handleModelTraining} disabled={loading || !selectedFile} primary icon={BrainCircuit}>
            {loading ? <Spinner /> : '모델 학습 및 최적화'}
          </Button>
          {modelTrainingResults && (
            <div style={{ marginTop: 20, borderTop: `1px solid ${COLOR.border}`, paddingTop: 20 }}>
              <h4 style={{ color: COLOR.primary, marginBottom: 10 }}>모델 비교 및 최적화:</h4>
              <p style={{ color: COLOR.text }}>최적 모델: <span style={{ fontWeight: 600 }}>{modelTrainingResults.best_model_name}</span></p>
              <p style={{ color: COLOR.text }}>파이프라인 저장 경로: <span style={{ fontWeight: 600 }}>{modelTrainingResults.pipeline_saved_path}</span></p>
              <h5 style={{ color: COLOR.secondary, marginTop: 15 }}>모델별 성능:</h5>
              <pre style={{ background: COLOR.dim, padding: 10, borderRadius: 4, fontSize: 12, overflowX: 'auto' }}>
                {JSON.stringify(modelTrainingResults.model_comparison, null, 2)}
              </pre>
              {/* TODO: modelTrainingResults.model_comparison을 사용하여 차트 그리기 */}
            </div>
          )}
        </Card>

        {/* 3. 예측 및 결과 */}
        <Card title="대장암 예측" icon={PieChart}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '20px' }}>
            <div>
              <label style={{ fontSize: '12px', color: COLOR.secondary }}>나이 (Age)</label>
              <input type="number" value={inputs.age} 
                onChange={e => setInputs({...inputs, age: e.target.value})}
                style={{ width: '100%', padding: '8px', background: COLOR.bg, border: `1px solid ${COLOR.border}`, color: COLOR.text }} />
            </div>
            <div>
              <label style={{ fontSize: '12px', color: COLOR.secondary }}>암 단계 (Cancer Stage)</label>
              <select value={inputs.cancerStage} 
                onChange={e => setInputs({...inputs, cancerStage: e.target.value})}
                style={{ width: '100%', padding: '8px', background: COLOR.bg, border: `1px solid ${COLOR.border}`, color: COLOR.text }}>
                <option>Stage I</option><option>Stage II</option><option>Stage III</option><option>Stage IV</option>
              </select>
            </div>
            <div>
              <label style={{ fontSize: '12px', color: COLOR.secondary }}>종양 크기 (Tumor Size mm)</label>
              <input type="number" value={inputs.tumorSize} 
                onChange={e => setInputs({...inputs, tumorSize: e.target.value})}
                style={{ width: '100%', padding: '8px', background: COLOR.bg, border: `1px solid ${COLOR.border}`, color: COLOR.text }} />
            </div>
            <div>
              <label style={{ fontSize: '12px', color: COLOR.secondary }}>비만도 (BMI)</label>
              <input type="number" value={inputs.bmi} 
                onChange={e => setInputs({...inputs, bmi: e.target.value})}
                style={{ width: '100%', padding: '8px', background: COLOR.bg, border: `1px solid ${COLOR.border}`, color: COLOR.text }} />
            </div>
            <div>
              <label style={{ fontSize: '12px', color: COLOR.secondary }}>당뇨 여부 (Diabetes)</label>
              <select value={inputs.diabetes} 
                onChange={e => setInputs({...inputs, diabetes: e.target.value})}
                style={{ width: '100%', padding: '8px', background: COLOR.bg, border: `1px solid ${COLOR.border}`, color: COLOR.text }}>
                <option>Yes</option><option>No</option>
              </select>
            </div>
          </div>
          <Button onClick={handlePrediction} disabled={loading} primary icon={BrainCircuit}>
            {loading ? <Spinner /> : '예측 실행'}
          </Button>
          {predictionResult && (
            <div style={{ marginTop: 20, borderTop: `1px solid ${COLOR.border}`, paddingTop: 20 }}>
              <h4 style={{ color: COLOR.primary, marginBottom: 10 }}>AI 진단 및 사망 위험 분석:</h4>
              <p style={{ fontSize: 16, fontWeight: 600, color: COLOR.text }}>
                {predictionResult.prediction === 1 ? (
                  <span style={{ color: COLOR.danger }}><XCircle size={18} style={{ verticalAlign: 'middle', marginRight: 5 }} />고위험군 (High Risk)</span>
                ) : (
                  <span style={{ color: COLOR.success }}><CheckCircle size={18} style={{ verticalAlign: 'middle', marginRight: 5 }} />저위험군 (Low Risk)</span>
                )}
              </p>
              <p style={{ color: COLOR.secondary, marginTop: 5 }}>
                예측 사망률: <span style={{ fontWeight: 600, color: COLOR.warning }}>{(predictionResult.probability * 100).toFixed(2)}%</span>
              </p>
              <div style={{ marginTop: 15, padding: 15, background: COLOR.dim, borderRadius: 8 }}>
                <h5 style={{ margin: '0 0 10px 0', color: COLOR.primary }}>AI 상담 소견</h5>
                <p style={{ fontSize: 13, lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>{predictionResult.advice}</p>
              </div>
            </div>
          )}
        </Card>

        {/* 4. 진단 기록 */}
        <Card title="진단 기록" icon={LineChart} color={COLOR.warning}>
          {diagnosisHistory.length === 0 ? (
            <p style={{ color: COLOR.secondary }}>아직 진단 기록이 없습니다.</p>
          ) : (
            <div style={{ maxHeight: 300, overflowY: 'auto', paddingRight: 10 }}>
              {diagnosisHistory.map((record) => (
                <div key={record.id} style={{
                  background: COLOR.bg, border: `1px solid ${COLOR.border}`, borderRadius: 6,
                  padding: 10, marginBottom: 10,
                }}>
                  <p style={{ fontSize: 14, fontWeight: 600, color: COLOR.text }}>
                    {record.title || `예측 결과: ${record.result}`}
                  </p>
                  <p style={{ fontSize: 12, color: COLOR.secondary }}>
                    확률: {(record.confidence * 100).toFixed(2)}%
                  </p>
                  <p style={{ fontSize: 10, color: COLOR.dim, marginTop: 5 }}>
                    {new Date(record.createdAt).toLocaleString()}
                  </p>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}