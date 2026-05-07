import React, { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Upload, Activity, FileText, ChevronRight, AlertCircle, Database, LayoutGrid, CheckSquare } from 'lucide-react';
import axios from 'axios';

// =====================================================================
// 담당자: DH (김담현) - 허리디스크 정밀 분석 페이지 (문진표 통합 버전)
// =====================================================================

export default function SpineDiskPage() {
  const [image, setImage] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState(null);

  // [NEW] 문진표 상태 관리
  const [clinicalData, setClinicalData] = useState({
    redFlag: [],
    symptoms: [],
    treatmentHistory: ''
  });

  // 문진표 체크박스 핸들러
  const handleCheckboxChange = (category, value) => {
    setClinicalData(prev => {
      const isChecked = prev[category].includes(value);
      if (isChecked) {
        return { ...prev, [category]: prev[category].filter(item => item !== value) };
      } else {
        return { ...prev, [category]: [...prev[category], value] };
      }
    });
  };

  const handleRadioChange = (value) => {
    setClinicalData(prev => ({ ...prev, treatmentHistory: value }));
  };

  // 템플릿 데이터 (테스트용)
  const detailedResults = {
    "Spinal Canal Stenosis": { "Normal_Mild": 0.03, "Moderate": 0.44, "Severe": 0.12 },
    "Neural Foraminal Narrowing": { "Normal_Mild": 0.03, "Moderate": 0.02, "Severe": 0.03 },
    "Subarticular Stenosis": { "Normal_Mild": 0.03, "Moderate": 0.03, "Severe": 0.04 }
  };

  /*
  const chartData = Object.keys(detailedResults).map(key => ({
    name: key.split(' ')[0],
    value: Math.max(...Object.values(detailedResults[key])) * 100,
    color: key === "Spinal Canal Stenosis" ? '#fbbf24' : '#10b981'
  }));
*/

  const handleUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImage(URL.createObjectURL(file));
      setSelectedFile(file);
      setResult(null);
    }
  };

  const runAnalysis = async () => {
    setIsAnalyzing(true);

    const formData = new FormData();
    formData.append("file", selectedFile);

    // [NEW] 문진표 데이터를 JSON 문자열로 변환하여 FormData에 추가
    formData.append("clinicalData", JSON.stringify(clinicalData));

    try {
      const response = await axios.post('http://192.168.0.13:8000/ai/spine/analyze', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setResult(response.data);
    } catch (error) {
      console.error("분석 중 에러 발생:", error);
      alert("분석 서버와 연결할 수 없습니다. 템플릿 데이터를 표시합니다.");
      setResult(detailedResults);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
      <div className="max-w-2xl mx-auto flex items-center justify-center min-h-[60vh] py-10">
        <div className="text-center bg-[#0f172a] border border-slate-800 rounded-2xl p-8 w-full shadow-2xl">

          {/* 헤더 */}
          <div className="mb-8">
            <div className="flex justify-center mb-4">
              <div className="bg-slate-800 p-3 rounded-full">
                <Activity className="text-blue-400" size={32} />
              </div>
            </div>
            <h2 className="text-2xl font-bold text-slate-200 mb-1">통합 척추 협착증 AI 진단</h2>
            <p className="text-slate-500 text-sm">담당: 김담현 (DH) | DL Vision + LLM RAG</p>
          </div>

          {!result ? (
              /* 업로드 및 문진표 작성 단계 */
              <div className="space-y-6 text-left">
                {/* 1. MRI 업로드 */}
                <div className="border-2 border-dashed border-slate-700 rounded-xl p-6 bg-slate-900/50 hover:bg-slate-900 transition-all cursor-pointer relative text-center">
                  {image ? (
                      <img src={image} alt="MRI Preview" className="max-h-48 mx-auto rounded-lg shadow-lg" />
                  ) : (
                      <div className="py-6">
                        <Upload className="mx-auto text-slate-600 mb-2" size={32} />
                        <p className="text-slate-400 text-sm">MRI 이미지를 업로드하세요</p>
                      </div>
                  )}
                  <input type="file" onChange={handleUpload} className="absolute inset-0 opacity-0 cursor-pointer" />
                </div>

                {/* [NEW] 2. 임상 증상 문진표 (체크박스) */}
                {image && (
                    <div className="bg-slate-900 p-5 rounded-xl border border-slate-800 space-y-4 animate-in fade-in">
                      <h3 className="text-slate-300 font-bold flex items-center gap-2 border-b border-slate-800 pb-2">
                        <CheckSquare size={16} className="text-blue-400"/> 환자 임상 증상 체크
                      </h3>

                      {/* Red Flag */}
                      <div>
                        <p className="text-xs text-red-400 font-bold mb-2">🚨 Red Flag (응급/위험 징후)</p>
                        <label className="flex items-center gap-2 text-sm text-slate-300 mb-1 cursor-pointer hover:text-white">
                          <input type="checkbox" className="accent-red-500" onChange={() => handleCheckboxChange('redFlag', '대소변 장애')} /> 대소변 기능 장애
                        </label>
                        <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer hover:text-white">
                          <input type="checkbox" className="accent-red-500" onChange={() => handleCheckboxChange('redFlag', '진행성 하지 마비')} /> 진행성 하지 마비 (근력 저하)
                        </label>
                      </div>

                      {/* 일반 증상 */}
                      <div className="pt-2">
                        <p className="text-xs text-amber-400 font-bold mb-2">🟡 주요 임상 증상</p>
                        <label className="flex items-center gap-2 text-sm text-slate-300 mb-1 cursor-pointer hover:text-white">
                          <input type="checkbox" className="accent-blue-500" onChange={() => handleCheckboxChange('symptoms', '하지 방사통')} /> 하지 방사통 (다리 저림)
                        </label>
                        <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer hover:text-white">
                          <input type="checkbox" className="accent-blue-500" onChange={() => handleCheckboxChange('symptoms', '간헐적 파행')} /> 간헐적 파행 (보행 시 통증으로 쉬어야 함)
                        </label>
                      </div>

                      {/* 과거 치료력 */}
                      <div className="pt-2">
                        <p className="text-xs text-blue-400 font-bold mb-2">🔵 기존 보존적 치료 이력</p>
                        <div className="flex gap-4">
                          <label className="flex items-center gap-1 text-sm text-slate-300 cursor-pointer hover:text-white">
                            <input type="radio" name="treatment" value="없음" className="accent-blue-500" onChange={() => handleRadioChange('없음')} /> 없음
                          </label>
                          <label className="flex items-center gap-1 text-sm text-slate-300 cursor-pointer hover:text-white">
                            <input type="radio" name="treatment" value="6주 미만" className="accent-blue-500" onChange={() => handleRadioChange('6주 미만')} /> 6주 미만
                          </label>
                          <label className="flex items-center gap-1 text-sm text-slate-300 cursor-pointer hover:text-white">
                            <input type="radio" name="treatment" value="6주 이상 실패" className="accent-blue-500" onChange={() => handleRadioChange('6주 이상 실패')} /> 6주 이상 차도 없음
                          </label>
                        </div>
                      </div>
                    </div>
                )}

                <button onClick={runAnalysis} disabled={!image || isAnalyzing}
                        className={`w-full py-4 rounded-xl font-bold transition-all flex items-center justify-center gap-2 ${
                            !image ? 'bg-slate-800 text-slate-600' : 'bg-blue-600 text-white hover:bg-blue-500 shadow-lg shadow-blue-900/20'
                        }`}>
                  {isAnalyzing ? <span className="animate-pulse text-sm">AI 모델 및 LLM 종합 분석 중...</span> : <>통합 분석 시작 <ChevronRight size={18} /></>}
                </button>
              </div>
          ) : (
              /* 결과 화면 (기존과 동일하게 유지하되, 나중에 RAG 리포트를 추가로 렌더링하면 됨) */
              <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700 text-left">
                {/* ... 기존 시각화 차트 및 그리드 코드 유지 ... */}

                {/* [NEW] LLM 통합 소견 노출부 */}
                <div className="bg-blue-600/10 border-l-4 border-blue-500 p-5 rounded-r-xl">
                  <div className="flex items-center gap-2 mb-2 text-blue-400">
                    <FileText size={16} />
                    <span className="font-bold text-xs uppercase">AI CDSS Final Report (Vision + Text)</span>
                  </div>
                  <p className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">
                    {/* 백엔드에서 받은 최종 리포트를 여기에 뿌려줍니다. */}
                    {result.final_report || "통합 분석 결과를 가져오는 중입니다..."}
                  </p>
                </div>

                <button onClick={() => {setResult(null); setImage(null);}} className="w-full text-slate-600 text-xs hover:text-slate-400 py-2 transition-colors">
                  새로운 영상 분석하기
                </button>
              </div>
          )}
        </div>
      </div>
  );
}