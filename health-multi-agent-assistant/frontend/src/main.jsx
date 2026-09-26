import React, {useRef, useState} from "react";
import {createRoot} from "react-dom/client";
import "./styles.css";

const configuredApi=import.meta.env.VITE_API_URL;
const API=configuredApi ? (configuredApi.startsWith("http") ? configuredApi : `https://${configuredApi}`) : "https://health-assisst.onrender.com";
const LANGUAGES={
  en:{name:"English",speak:"Speak symptoms",stop:"Stop recording",listening:"Recording...",placeholder:"Your offline transcript will appear here..."},
  te:{name:"తెలుగు",speak:"లక్షణాలను మాట్లాడండి",stop:"రికార్డింగ్ ఆపండి",listening:"రికార్డింగ్ అవుతోంది...",placeholder:"మీ ఆఫ్‌లైన్ ట్రాన్స్‌క్రిప్ట్ ఇక్కడ కనిపిస్తుంది..."},
  hi:{name:"हिंदी",speak:"लक्षण बोलें",stop:"रिकॉर्डिंग रोकें",listening:"रिकॉर्ड हो रहा है...",placeholder:"आपका ऑफलाइन ट्रांसक्रिप्ट यहां दिखाई देगा..."}
};
const DOCTOR_FIELDS=[
  {key:"assessment",label:"Clinical assessment",type:"textarea",placeholder:"Enter the clinical assessment..."},
  {key:"medicine",label:"Medicine",placeholder:"Enter only if clinically appropriate..."},
  {key:"dosage",label:"Dosage",placeholder:"e.g. 500 mg"},
  {key:"frequency",label:"Frequency",placeholder:"e.g. Twice daily"},
  {key:"duration",label:"Duration",placeholder:"e.g. 3 days"},
  {key:"instructions",label:"Instructions",type:"textarea",placeholder:"Enter advice and follow-up instructions..."}
];

function App(){
  const [tab,setTab]=useState("patient");
  const [form,setForm]=useState({name:"Ravi",age:25,language:"en",symptoms:"",duration:"",allergies:"",current_medicines:"",medical_history:""});
  const [result,setResult]=useState(null);
  const [doctor,setDoctor]=useState({assessment:"",medicine:"",dosage:"",frequency:"",duration:"",instructions:""});
  const [sent,setSent]=useState(false);
  const [submitting,setSubmitting]=useState(false);
  const [submitError,setSubmitError]=useState("");
  const [listening,setListening]=useState(false);
  const [transcribing,setTranscribing]=useState(false);
  const [voiceError,setVoiceError]=useState("");
  const [cases,setCases]=useState([]);
  const recorderRef=useRef(null);
  const audioChunksRef=useRef([]);
  const streamRef=useRef(null);
  const selectedLanguage=LANGUAGES[form.language] || LANGUAGES.en;

  async function loadCases(){
    try{
      const response=await fetch(API+"/api/cases");
      if(response.ok) setCases(await response.json());
    }catch(error){
      console.error("Unable to load patient cases",error);
    }
  }

  const update=(e)=>setForm({...form,[e.target.name]:e.target.value});

  async function transcribeRecording(blob){
    setTranscribing(true);
    const body=new FormData();
    body.append("audio",blob,"symptoms.webm");
    body.append("language",form.language);
    try{
      const response=await fetch(API+"/api/transcribe",{method:"POST",body});
      if(!response.ok) throw new Error(`Transcription failed (${response.status})`);
      const data=await response.json();
      if(!data.text) throw new Error("No speech was detected.");
      setForm(current=>({...current,symptoms:data.text}));
    }catch(error){
      setVoiceError(`${error.message} Check that the offline Whisper backend is running.`);
    }finally{
      setTranscribing(false);
    }
  }

  async function toggleVoice(){
    setVoiceError("");
    if(listening){
      recorderRef.current.stop();
    }else{
      try{
        if(!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder){
          throw new Error("Audio recording is not supported in this browser.");
        }
        const stream=await navigator.mediaDevices.getUserMedia({audio:true});
        streamRef.current=stream;
        audioChunksRef.current=[];
        const recorder=new MediaRecorder(stream);
        recorder.ondataavailable=(event)=>{
          if(event.data.size>0) audioChunksRef.current.push(event.data);
        };
        recorder.onstop=()=>{
          stream.getTracks().forEach(track=>track.stop());
          const blob=new Blob(audioChunksRef.current,{type:recorder.mimeType || "audio/webm"});
          setListening(false);
          transcribeRecording(blob);
        };
        recorderRef.current=recorder;
        recorder.start();
        setListening(true);
      }catch(error){
        setVoiceError(error.name==="NotAllowedError"
          ? "Microphone access was blocked. Allow microphone access and try again."
          : error.message || "Unable to start the microphone.");
        setListening(false);
      }
    }
  }

  async function analyze(e){
    e.preventDefault();
    if(listening || transcribing){
      setSubmitError("Please stop recording and wait for the offline transcription to finish.");
      return;
    }
    setSubmitError("");
    setSubmitting(true);
    try{
      const r=await fetch(API+"/api/analyze",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({...form,age:Number(form.age)})
      });
      const data=await r.json();
      if(!r.ok){
        const detail=Array.isArray(data.detail) ? data.detail.map(item=>item.msg).join(", ") : data.detail;
        throw new Error(detail || `Request failed (${r.status})`);
      }
      setResult(data);
      await loadCases();
      setTab("doctor");
    }catch(error){
      setSubmitError(`Could not prepare the case: ${error.message}. Make sure the backend is running on port 8000.`);
    }finally{
      setSubmitting(false);
    }
  }
  async function approve(e){
    e.preventDefault();
    await fetch(API+"/api/doctor/recommend",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({...doctor,case_id:result?.case_id})});
    await loadCases();
    setSent(true);
  }

  return <div className="app">
    <video className="background-video" autoPlay muted loop playsInline aria-hidden="true">
      <source src="/videos/health-background.mp4" type="video/mp4" />
    </video>
    <header><div><h1>AI Health Assistant</h1><p>Multilingual multi-agent • Doctor-in-the-loop</p></div>
      <nav><button onClick={()=>setTab("patient")} className={tab==="patient"?"active":""}>New Patient</button><button onClick={()=>{loadCases();setTab("cases")}} className={tab==="cases"?"active":""}>Patient Cases ({cases.length})</button><button onClick={()=>setTab("doctor")} className={tab==="doctor"?"active":""}>Doctor Review</button>{sent && <button onClick={()=>setTab("delivery")} className={tab==="delivery"?"active":""}>Patient Delivery</button>}</nav>
    </header>
    <main>
      {tab==="patient" &&       <section className="card" lang={form.language}><h2>Patient Intake</h2><p className="muted">English • తెలుగు • हिंदी</p>
        <form onSubmit={analyze}>
          <div className="grid"><label>Name<input name="name" value={form.name} onChange={update}/></label><label>Age<input type="number" name="age" value={form.age} onChange={update}/></label>
          <label>Language<select name="language" value={form.language} onChange={update}><option value="en">English</option><option value="te">తెలుగు (Telugu)</option><option value="hi">हिंदी (Hindi)</option></select></label>
          <label>Duration<input name="duration" value={form.duration} onChange={update} placeholder="e.g. 2 days"/></label></div>
          <label>Symptoms
            <button type="button" className={`voice-button ${listening?"listening":""}`} onClick={toggleVoice} aria-pressed={listening} disabled={transcribing}>
              <span aria-hidden="true">🎙</span> {transcribing ? "Transcribing offline..." : listening ? selectedLanguage.stop : selectedLanguage.speak}
            </button>
            <textarea name="symptoms" value={form.symptoms} onChange={update} required placeholder={listening ? selectedLanguage.listening : selectedLanguage.placeholder}/>
          </label>
          {voiceError && <p className="voice-error" role="alert">{voiceError}</p>}
          {submitError && <p className="voice-error" role="alert">{submitError}</p>}
          <label>Allergies<textarea name="allergies" value={form.allergies} onChange={update}/></label>
          <label>Current medicines<textarea name="current_medicines" value={form.current_medicines} onChange={update}/></label>
          <label>Medical history<textarea name="medical_history" value={form.medical_history} onChange={update}/></label>
          <button type="submit" className="primary" disabled={submitting || listening || transcribing}>
            {submitting ? "Preparing case..." : "Prepare for Doctor Review"}
          </button>
        </form>
      </section>}

      {tab==="cases" && <section className="card"><h2>Patient Cases</h2><p className="muted">Saved cases can contain multiple patients and different conditions.</p>{cases.length===0 ? <p>No patient cases saved yet.</p> : <div className="case-list">{cases.map(item=><button className="case-item" key={item.id} onClick={()=>{setResult(item.analysis);setDoctor(item.recommendation || {assessment:"",medicine:"",dosage:"",frequency:"",duration:"",instructions:""});setTab("doctor")}}><b>Case #{item.id}: {item.patient.name}</b><span>{item.patient.age} years • {item.patient.symptoms}</span><small>{new Date(item.created_at).toLocaleString()}</small></button>)}</div>}</section>}

      {tab==="doctor" && <section className="card doctor-review-card" lang={result?.language || "en"}>
        <video className="doctor-review-video" autoPlay muted loop playsInline aria-hidden="true">
          <source src="/videos/doctor-review-background.mp4" type="video/mp4" />
        </video>
        <div className="doctor-review-content"><h2>Doctor Review</h2>
        {!result ? <p className="muted">Submit a patient case first.</p> : <>
          <div className="alert"><b>Triage:</b> {result.triage}. {result.message}</div>
          <h3>Patient Summary</h3><pre>{JSON.stringify(result.patient_summary,null,2)}</pre>
          {result.detected_symptoms?.length > 0 && <p className="detected-symptoms"><b>Detected symptoms:</b> {result.detected_symptoms.join(", ")}</p>}
          <h3>Reference Conditions</h3><p>{result.possible_reference_conditions?.join(", ") || "No reference condition matched."}</p>
          {result.treatment_references?.length > 0 && <div className="treatment-reference">
            <h3>Clinician Reference: Treatment Examples</h3>
            <p className="reference-warning">These are educational examples only, not a prescription. Confirm diagnosis, allergies, current medicines, contraindications, and local guidance before prescribing.</p>
            <ul>{result.treatment_references.map(reference=><li key={reference.condition}><b>{reference.condition}:</b> {reference.examples}</li>)}</ul>
          </div>}
          {result.structured_treatments?.map(treatment=><div className="treatment-reference" key={treatment.condition}>
            <h3>{treatment.condition}: Clinician Treatment Options</h3>
            <ul>{treatment.treatment_options.map(option=><li key={option.medicine}><b>{option.medicine}</b> ({option.type})</li>)}</ul>
            <p className="reference-warning">Doctor approval is required. These options are not an automatic prescription.</p>
          </div>)}
          {result.medicine_information?.items?.length > 0 && <div className="treatment-reference">
            <h3>Common Medicine Information: Doctor Reference</h3>
            <p className="reference-warning">Educational information only. These are not automatic recommendations. A licensed doctor must select any medicine after reviewing the patient's allergies, age, pregnancy status when relevant, current medicines, and medical conditions.</p>
            <ul>{result.medicine_information.items.map(item=><li key={item.area}><b>{item.area}:</b> {item.medicines.join(", ")}{item.prescription ? " (prescription medicine; clinician evaluation required)" : ""}</li>)}</ul>
            <h4>Safety checks</h4>
            <ul>{result.medicine_information.safety_checks.map(check=><li key={check}>{check}</li>)}</ul>
          </div>}
          {result.dataset_references?.length > 0 && <div className="treatment-reference">
            <h3>Dataset Reference Matches</h3>
            <p className="reference-warning">{result.dataset_notice}</p>
            <ul>{result.dataset_references.map(reference=><li key={reference.patient_id}><b>{reference.possible_condition}</b> — {reference.symptoms}; severity: {reference.severity}; emergency: {reference.emergency}. <span>{reference.recommended_action}</span></li>)}</ul>
          </div>}
          {result.medicine_references?.length > 0 && <div className="treatment-reference">
            <h3>Disease and Tablet Reference: Doctor Only</h3>
            <p className="reference-warning">{result.medicine_dataset_notice}</p>
            <ul>{result.medicine_references.map(reference=><li key={reference.disease_id}><b>{reference.disease}</b> — {reference.medicine_or_tablet}; dosage: {reference.dosage}; route: {reference.route}. {reference.treatment_note}</li>)}</ul>
          </div>}
          <h3>Doctor Description</h3><p className="doctor-description">{result.doctor_note}</p>
          <div className="notice">{result.medicine_policy}</div>
          <form className="doctor-description-form" onSubmit={approve}><h3>Doctor Recommendation</h3>
            {DOCTOR_FIELDS.map(({key,label,type,placeholder})=><label key={key}>{label}
              {type==="textarea"
                ? <textarea value={doctor[key]} placeholder={placeholder} required={key==="assessment"} onChange={e=>setDoctor({...doctor,[key]:e.target.value})}/>
                : <input value={doctor[key]} placeholder={placeholder} onChange={e=>setDoctor({...doctor,[key]:e.target.value})}/>}
            </label>)}
            <button className="primary">Approve & Send to Patient</button>
          </form>
          {sent && <div className="success">Doctor recommendation recorded for patient delivery.</div>}
        </>}
        </div>
      </section>}

      {tab==="delivery" && <section className="card delivery-card" lang={result?.language || "en"}>
        <h2>Patient Delivery</h2>
        <p className="success">Your doctor-approved recommendation is ready.</p>
        <h3>Doctor Assessment</h3>
        <p>{doctor.assessment}</p>
        <h3>Medicine and Instructions</h3>
        <dl className="delivery-details">
          <dt>Medicine</dt><dd>{doctor.medicine || "No medicine entered"}</dd>
          <dt>Dosage</dt><dd>{doctor.dosage || "Not specified"}</dd>
          <dt>Frequency</dt><dd>{doctor.frequency || "Not specified"}</dd>
          <dt>Duration</dt><dd>{doctor.duration || "Not specified"}</dd>
          <dt>Instructions</dt><dd>{doctor.instructions || "No additional instructions"}</dd>
        </dl>
        <p className="notice">Follow the doctor’s instructions. Contact a healthcare professional if symptoms worsen or you have concerns.</p>
      </section>}
    </main>
    <footer>Educational demo • Not a substitute for professional medical care</footer>
  </div>
}
createRoot(document.getElementById("root")).render(<App/>);
