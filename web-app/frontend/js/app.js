const API_BASE_URL='http://localhost:5000/api';
let selectedModel=null,availableModels=[],currentExtractionData=null,batchFiles=[],finetuneFiles=[],currentJobId=null;

const elements={
 modelSelector:document.getElementById('modelSelector'),
 modelInfo:document.getElementById('modelInfo'),
 uploadArea:document.getElementById('uploadArea'),
 fileInput:document.getElementById('fileInput'),
 imagePreview:document.getElementById('imagePreview'),
 previewImg:document.getElementById('previewImg'),
 extractBtn:document.getElementById('extractBtn'),
 batchExtractBtn:document.getElementById('batchExtractBtn'),
 actionButtons:document.getElementById('actionButtons'),
 resultsSection:document.getElementById('resultsSection'),
 errorSection:document.getElementById('errorSection'),
 loadingOverlay:document.getElementById('loadingOverlay'),
 batchModelSelect:document.getElementById('batchModelSelect'),
 useAllModels:document.getElementById('useAllModels'),
 finetuneModelSelect:document.getElementById('finetuneModelSelect')
};

async function init(){
 setupEventListeners();
 setupTabNavigation();
 setupBatchProcessing();
 setupFinetuning();
 await loadModels();
}

function setupEventListeners(){
 elements.fileInput.addEventListener('change',handleFileSelect);
 elements.uploadArea.addEventListener('dragover',handleDragOver);
 elements.uploadArea.addEventListener('dragleave',handleDragLeave);
 elements.uploadArea.addEventListener('drop',handleDrop);
 elements.extractBtn?.addEventListener('click',handleExtract);
 elements.batchExtractBtn?.addEventListener('click',handleBatchExtract);
 document.getElementById('exportJson')?.addEventListener('click',()=>exportData('json'));
 document.getElementById('exportCsv')?.addEventListener('click',()=>exportData('csv'));
 document.getElementById('exportTxt')?.addEventListener('click',()=>exportData('txt'));
}

function setupTabNavigation(){
 const tabBtns=document.querySelectorAll('.tab-btn');
 tabBtns.forEach(btn=>{
  btn.addEventListener('click',()=>{
   const tabName=btn.dataset.tab;
   document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
   document.querySelectorAll('.tab-content').forEach(t=>t.classList.remove('active'));
   btn.classList.add('active');
   document.getElementById(`${tabName}Tab`).classList.add('active');
  });
 });
}

function setupBatchProcessing(){
 const batchFileInput=document.getElementById('batchFileInput');
 const batchUploadArea=document.getElementById('batchUploadArea');
 const processBatchBtn=document.getElementById('processBatchBtn');
 const clearBatchBtn=document.getElementById('clearBatchBtn');
 const sourceBtns=document.querySelectorAll('.source-btn');
 const cloudBtns=document.querySelectorAll('.cloud-btn');

 batchFileInput?.addEventListener('change',(e)=>{
  batchFiles=Array.from(e.target.files);
  displayBatchFiles();
  processBatchBtn.disabled=batchFiles.length===0;
 });

 batchUploadArea?.addEventListener('click',()=>batchFileInput?.click());

 processBatchBtn?.addEventListener('click',processBatchImages);
 clearBatchBtn?.addEventListener('click',()=>{
  batchFiles=[];
  batchFileInput.value='';
  document.getElementById('batchFileList').classList.add('hidden');
  processBatchBtn.disabled=true;
 });

 sourceBtns.forEach(btn=>{
  btn.addEventListener('click',()=>{
   const source=btn.dataset.source;
   document.querySelectorAll('.source-btn').forEach(b=>b.classList.remove('active'));
   document.querySelectorAll('.source-content').forEach(c=>c.classList.remove('active'));
   btn.classList.add('active');
   document.getElementById(`${source}Source`).classList.add('active');
  });
 });

 cloudBtns.forEach(btn=>{
  btn.addEventListener('click',()=>loadCloudFiles(btn.dataset.provider));
 });

 elements.useAllModels?.addEventListener('change',(e)=>{
  if(elements.batchModelSelect){
   elements.batchModelSelect.disabled=e.target.checked;
  }
 });
}

function setupFinetuning(){
 const ftModeRadios=document.querySelectorAll('input[name="ftMode"]');
 const ftFileInput=document.getElementById('ftFileInput');
 const ftUploadArea=document.getElementById('ftUploadArea');
 const startFinetuneBtn=document.getElementById('startFinetuneBtn');
 const viewJobsBtn=document.getElementById('viewJobsBtn');
 const exportModelBtn=document.getElementById('exportModelBtn');
 const modalClose=document.querySelector('.modal-close');

 ftModeRadios.forEach(radio=>{
  radio.addEventListener('change',(e)=>{
   const mode=e.target.value;
   document.querySelectorAll('.ft-config').forEach(c=>c.classList.remove('active'));
   document.getElementById(`${mode}FtConfig`).classList.add('active');
  });
 });

 ftFileInput?.addEventListener('change',(e)=>{
  finetuneFiles=Array.from(e.target.files);
  displayFinetuneFiles();
  startFinetuneBtn.disabled=finetuneFiles.length===0;
 });

 ftUploadArea?.addEventListener('click',()=>ftFileInput?.click());
 startFinetuneBtn?.addEventListener('click',startFinetuning);
 viewJobsBtn?.addEventListener('click',viewTrainingJobs);
 exportModelBtn?.addEventListener('click',exportFinetunedModel);
 modalClose?.addEventListener('click',()=>document.getElementById('jobsModal').classList.add('hidden'));
}

function displayBatchFiles(){
 const fileList=document.getElementById('batchFileList');
 fileList.innerHTML='';
 fileList.classList.remove('hidden');
 batchFiles.forEach(file=>{
  const item=document.createElement('div');
  item.className='file-item';
  item.innerHTML=`<span>${file.name}</span><span>${(file.size/1024).toFixed(1)} KB</span>`;
  fileList.appendChild(item);
 });
}

function displayFinetuneFiles(){
 const fileList=document.getElementById('ftFileList');
 fileList.innerHTML='';
 fileList.classList.remove('hidden');
 finetuneFiles.forEach(file=>{
  const item=document.createElement('div');
  item.className='file-item';
  item.innerHTML=`<span>${file.name}</span><span>${(file.size/1024).toFixed(1)} KB</span>`;
  fileList.appendChild(item);
 });
}

async function processBatchImages(){
 if(batchFiles.length===0){showError('No files selected');return;}

 const useAllModelsChecked=elements.useAllModels?.checked;
 const selectedBatchModel=elements.batchModelSelect?.value;

 if(!useAllModelsChecked&&!selectedBatchModel){
  showError('Please select a model or enable "Extract with ALL models"');
  return;
 }

 const modelToUse=useAllModelsChecked?'all':selectedBatchModel;
 showLoading(true,`Processing ${batchFiles.length} images with ${useAllModelsChecked?'all models':selectedBatchModel}...`);

 const formData=new FormData();
 batchFiles.forEach(file=>formData.append('images',file));
 formData.append('model_id',modelToUse);
 formData.append('use_all_models',useAllModelsChecked?'true':'false');

 try{
  const response=await fetch(`${API_BASE_URL}/extract/batch-multi`,{method:'POST',body:formData});
  const data=await response.json();

  if(data.success){
   displayBatchResults(data);
   showSuccess(`Successfully processed ${data.images_count} images!`);
  }else{
   showError(data.error||'Batch processing failed');
  }
 }catch(error){
  console.error('Batch processing error:',error);
  showError('Failed to process batch images');
 }finally{
  showLoading(false);
 }
}

function displayBatchResults(data){
 const batchResults=document.getElementById('batchResults');
 const batchProgress=document.getElementById('batchProgress');
 batchProgress.classList.add('hidden');
 batchResults.classList.remove('hidden');
 batchResults.innerHTML='<h3>Batch Results</h3>';

 data.results.forEach(result=>{
  const item=document.createElement('div');
  item.className=`result-item ${result.extraction.success?'success':'error'}`;
  const extraction=result.extraction;

  if(extraction.success&&extraction.data){
   const d=extraction.data;
   item.innerHTML=`
    <h4>${result.filename}</h4>
    <p><strong>Store:</strong> ${d.store?.name||'-'}</p>
    <p><strong>Total:</strong> $${d.totals?.total||'-'}</p>
    <p><strong>Items:</strong> ${d.items?.length||0}</p>
    <p><strong>Time:</strong> ${d.processing_time?.toFixed(2)}s</p>
   `;
  }else{
   item.innerHTML=`<h4>${result.filename}</h4><p class="error">Error: ${extraction.error||'Processing failed'}</p>`;
  }
  batchResults.appendChild(item);
 });

 const exportBtn=document.createElement('button');
 exportBtn.className='btn btn-primary';
 exportBtn.textContent='Export All Results';
 exportBtn.onclick=()=>{
  const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'});
  const url=URL.createObjectURL(blob);
  const a=document.createElement('a');
  a.href=url;
  a.download=`batch_results_${new Date().toISOString().slice(0,10)}.json`;
  a.click();
  URL.revokeObjectURL(url);
 };
 batchResults.appendChild(exportBtn);
}

async function loadCloudFiles(provider){
 showError('Cloud storage integration is not yet implemented. This feature requires API integration with Google Drive, Dropbox, or AWS S3. See README for setup instructions.');
 return;

 showLoading(true,`Loading files from ${provider}...`);
 try{
  const response=await fetch(`${API_BASE_URL}/cloud/list`,{
   method:'POST',
   headers:{'Content-Type':'application/json'},
   body:JSON.stringify({provider,path:'/'})
  });
  const data=await response.json();

  if(data.success){
   displayCloudFiles(data.files,provider);
   showSuccess(`Found ${data.files.length} files in ${provider}`);
  }else{
   if(data.is_placeholder){
    showError('Cloud storage not implemented. Please use local file upload.');
   }else{
    showError(data.error||'Failed to load cloud files');
   }
  }
 }catch(error){
  console.error('Cloud files error:',error);
  showError('Failed to connect to cloud storage');
 }finally{
  showLoading(false);
 }
}

function displayCloudFiles(files,provider){
 const cloudFileList=document.getElementById('cloudFileList');
 cloudFileList.innerHTML='<h4>Available Files</h4>';
 cloudFileList.classList.remove('hidden');

 files.forEach(file=>{
  const item=document.createElement('div');
  item.className='file-item';
  item.innerHTML=`
   <span>${file.name}</span>
   <span>${(file.size/1024).toFixed(1)} KB</span>
   <button class="btn btn-secondary" onclick="downloadCloudFile('${provider}','${file.path}')">Use</button>
  `;
  cloudFileList.appendChild(item);
 });
}

async function startFinetuning(){
 if(finetuneFiles.length===0){showError('Please upload training images');return;}

 const selectedFinetuneModel=elements.finetuneModelSelect?.value;
 if(!selectedFinetuneModel){
  showError('Please select a model to finetune');
  return;
 }

 const mode=document.querySelector('input[name="ftMode"]:checked').value;

 if(mode==='cloud'){
  showError('Cloud-based training is not yet implemented. Please use Local Computer mode or integrate with HuggingFace/Replicate APIs.');
  return;
 }

 const epochs=parseInt(document.getElementById('ftEpochs').value);
 const batchSize=parseInt(document.getElementById('ftBatchSize').value);
 const learningRate=parseFloat(document.getElementById('ftLearningRate').value);

 showLoading(true,'Preparing finetuning job...');

 try{
  const prepareResponse=await fetch(`${API_BASE_URL}/finetune/prepare`,{
   method:'POST',
   headers:{'Content-Type':'application/json'},
   body:JSON.stringify({model_id:selectedFinetuneModel,mode,config:{epochs,batchSize,learningRate}})
  });
  const prepareData=await prepareResponse.json();

  if(!prepareData.success){showError(prepareData.error);return;}

  currentJobId=prepareData.job_id;
  const formData=new FormData();
  finetuneFiles.forEach(file=>formData.append('images',file));
  formData.append('labels',JSON.stringify({}));

  const addDataResponse=await fetch(`${API_BASE_URL}/finetune/${currentJobId}/add-data`,{method:'POST',body:formData});
  const addDataResult=await addDataResponse.json();

  if(!addDataResult.success){showError(addDataResult.error);return;}

  const startResponse=await fetch(`${API_BASE_URL}/finetune/${currentJobId}/start`,{
   method:'POST',
   headers:{'Content-Type':'application/json'},
   body:JSON.stringify({epochs,batch_size:batchSize,learning_rate:learningRate})
  });
  const startData=await startResponse.json();

  if(startData.success){
   showSuccess('Finetuning started!');
   monitorFinetuning(currentJobId);
  }else{
   showError(startData.error||'Failed to start finetuning');
  }
 }catch(error){
  console.error('Finetuning error:',error);
  showError('Failed to start finetuning');
 }finally{
  showLoading(false);
 }
}

async function monitorFinetuning(jobId){
 const progressSection=document.getElementById('finetuneProgress');
 const progressBar=document.getElementById('ftProgressBar');
 const progressText=document.getElementById('ftProgressText');
 const metricsDisplay=document.getElementById('ftMetrics');

 progressSection.classList.remove('hidden');

 const checkProgress=async()=>{
  try{
   const response=await fetch(`${API_BASE_URL}/finetune/${jobId}/status`);
   const data=await response.json();

   if(data.success){
    const job=data.job;
    progressBar.style.width=`${job.progress}%`;
    progressText.textContent=`Progress: ${job.progress}% - ${job.status}`;

    if(job.status==='completed'){
     metricsDisplay.classList.remove('hidden');
     metricsDisplay.innerHTML=`
      <h4>Training Metrics</h4>
      <p><strong>Accuracy:</strong> ${(job.metrics?.accuracy*100).toFixed(2)}%</p>
      <p><strong>Loss:</strong> ${job.metrics?.loss?.toFixed(4)}</p>
      <p><strong>Samples:</strong> ${job.samples_count}</p>
     `;
     document.getElementById('finetuneResults').classList.remove('hidden');
     document.getElementById('ftResultsContent').innerHTML=`<p>Model finetuning completed successfully!</p>`;
     clearInterval(progressInterval);
    }else if(job.status==='failed'){
     showError('Finetuning failed: '+job.error);
     clearInterval(progressInterval);
    }
   }
  }catch(error){
   console.error('Progress check error:',error);
  }
 };

 const progressInterval=setInterval(checkProgress,2000);
 checkProgress();
}

async function viewTrainingJobs(){
 try{
  const response=await fetch(`${API_BASE_URL}/finetune/jobs`);
  const data=await response.json();

  if(data.success){
   const jobsList=document.getElementById('jobsList');
   jobsList.innerHTML='';

   if(data.jobs.length===0){
    jobsList.innerHTML='<p>No training jobs found</p>';
   }else{
    data.jobs.forEach(job=>{
     const item=document.createElement('div');
     item.className='job-item';
     item.innerHTML=`
      <h3>${job.model_id}<span class="job-status ${job.status}">${job.status}</span></h3>
      <p><strong>Job ID:</strong> ${job.id}</p>
      <p><strong>Progress:</strong> ${job.progress}%</p>
      <p><strong>Samples:</strong> ${job.samples}</p>
      <p><strong>Created:</strong> ${new Date(job.created*1000).toLocaleString()}</p>
     `;
     jobsList.appendChild(item);
    });
   }

   document.getElementById('jobsModal').classList.remove('hidden');
  }
 }catch(error){
  console.error('Jobs fetch error:',error);
  showError('Failed to load training jobs');
 }
}

async function exportFinetunedModel(){
 if(!currentJobId){showError('No completed training job');return;}

 try{
  window.location.href=`${API_BASE_URL}/finetune/${currentJobId}/export`;
  showSuccess('Model export started');
 }catch(error){
  console.error('Export error:',error);
  showError('Failed to export model');
 }
}

async function loadModels(){
 try{
  const response=await fetch(`${API_BASE_URL}/models`);
  const data=await response.json();
  if(data.success){
   availableModels=data.models;
   selectedModel=data.current_model||data.default_model;
   renderModels();
  }else{
   showError('Failed to load models');
  }
 }catch(error){
  console.error('Error loading models:',error);
  showError('Failed to connect to API server');
 }
}

function renderModels(){
 if(availableModels.length===0){
  elements.modelSelector.innerHTML='<p class="loading">No models available</p>';
  return;
 }

 elements.modelSelector.innerHTML='';
 availableModels.forEach(model=>{
  const card=document.createElement('div');
  card.className=`model-card ${model.id===selectedModel?'selected':''}`;
  card.onclick=()=>selectModel(model.id);
  const badgeClass=`badge-${model.type}`;
  card.innerHTML=`
   <h4>${model.name}</h4>
   <p>${model.description}</p>
   <span class="model-badge ${badgeClass}">${model.type.toUpperCase()}</span>
  `;
  elements.modelSelector.appendChild(card);
 });
 updateModelInfo();
 populateModelDropdowns();
}

function populateModelDropdowns(){
 if(elements.batchModelSelect){
  elements.batchModelSelect.innerHTML='<option value="">Select a model</option>';
  availableModels.forEach(model=>{
   const option=document.createElement('option');
   option.value=model.id;
   option.textContent=`${model.name} (${model.type})`;
   if(model.id===selectedModel){
    option.selected=true;
   }
   elements.batchModelSelect.appendChild(option);
  });
 }

 if(elements.finetuneModelSelect){
  elements.finetuneModelSelect.innerHTML='<option value="">Select a model</option>';
  const finetuneableModels=availableModels.filter(m=>['donut','florence','easyocr','paddle'].includes(m.type));
  finetuneableModels.forEach(model=>{
   const option=document.createElement('option');
   option.value=model.id;
   option.textContent=`${model.name} (${model.type})`;
   if(model.id===selectedModel){
    option.selected=true;
   }
   elements.finetuneModelSelect.appendChild(option);
  });
 }
}

async function selectModel(modelId){
 try{
  const response=await fetch(`${API_BASE_URL}/models/select`,{
   method:'POST',
   headers:{'Content-Type':'application/json'},
   body:JSON.stringify({model_id:modelId})
  });
  const data=await response.json();
  if(data.success){
   selectedModel=modelId;
   renderModels();
  }else{
   showError(`Failed to select model: ${data.error}`);
  }
 }catch(error){
  console.error('Error selecting model:',error);
  showError('Failed to select model');
 }
}

function updateModelInfo(){
 const model=availableModels.find(m=>m.id===selectedModel);
 if(model){
  const capabilities=model.capabilities;
  const capList=Object.entries(capabilities).filter(([_,value])=>value).map(([key])=>key.replace('_',' ')).join(', ');
  elements.modelInfo.innerHTML=`<strong>Selected Model:</strong> ${model.name}<br><strong>Capabilities:</strong> ${capList||'Basic extraction'}`;
 }
}

function handleFileSelect(event){
 const file=event.target.files[0];
 if(file)processFile(file);
}

function handleDragOver(event){
 event.preventDefault();
 elements.uploadArea.classList.add('dragover');
}

function handleDragLeave(event){
 event.preventDefault();
 elements.uploadArea.classList.remove('dragover');
}

function handleDrop(event){
 event.preventDefault();
 elements.uploadArea.classList.remove('dragover');
 const file=event.dataTransfer.files[0];
 if(file&&file.type.startsWith('image/'))processFile(file);
 else showError('Please drop an image file');
}

function processFile(file){
 const maxSize=100*1024*1024;
 if(file.size>maxSize){showError('File size exceeds 100MB');return;}

 const reader=new FileReader();
 reader.onload=(e)=>{
  elements.previewImg.src=e.target.result;
  elements.imagePreview.classList.remove('hidden');
  elements.extractBtn.disabled=false;
  elements.batchExtractBtn.disabled=false;
 };
 reader.readAsDataURL(file);
 elements.fileInput.file=file;
}

async function handleExtract(){
 const file=elements.fileInput.files[0];
 if(!file){showError('Please select an image first');return;}
 if(!selectedModel){showError('Please select a model first');return;}

 showLoading(true);
 hideError();
 elements.resultsSection.classList.add('hidden');

 try{
  const formData=new FormData();
  formData.append('image',file);
  formData.append('model_id',selectedModel);

  const response=await fetch(`${API_BASE_URL}/extract`,{method:'POST',body:formData});
  const data=await response.json();

  if(data.success&&data.data){
   currentExtractionData=data.data;
   displayResults(data.data);
  }else{
   showError(data.error||'Extraction failed');
  }
 }catch(error){
  console.error('Extraction error:',error);
  showError('Failed to extract receipt data');
 }finally{
  showLoading(false);
 }
}

async function handleBatchExtract(){
 const file=elements.fileInput.files[0];
 if(!file){showError('Please select an image first');return;}

 showLoading(true,'Processing with ALL models...');
 hideError();

 try{
  const formData=new FormData();
  formData.append('image',file);

  const response=await fetch(`${API_BASE_URL}/extract/batch`,{method:'POST',body:formData});
  const data=await response.json();

  if(data.success){
   downloadBatchResults(data);
   showSuccess(`Successfully extracted with ${data.models_count} models!`);
  }else{
   showError(data.error||'Batch extraction failed');
  }
 }catch(error){
  console.error('Batch extraction error:',error);
  showError('Failed to perform batch extraction');
 }finally{
  showLoading(false);
 }
}

function downloadBatchResults(data){
 const timestamp=new Date().toISOString().replace(/[:.]/g,'-').slice(0,-5);
 const filename=`batch_extraction_${timestamp}.json`;
 const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'});
 const url=URL.createObjectURL(blob);
 const a=document.createElement('a');
 a.href=url;
 a.download=filename;
 a.click();
 URL.revokeObjectURL(url);
}

function displayResults(data){
 document.getElementById('storeName').textContent=data.store?.name||'-';
 document.getElementById('storeAddress').textContent=data.store?.address||'-';
 document.getElementById('storePhone').textContent=data.store?.phone||'-';
 document.getElementById('transDate').textContent=data.date||'-';
 document.getElementById('transTime').textContent=data.time||'-';
 document.getElementById('total').textContent=data.totals?.total?`$${data.totals.total}`:'-';

 const processingInfo=document.getElementById('processingInfo');
 processingInfo.innerHTML=`<strong>Model:</strong> ${data.model} | <strong>Processing Time:</strong> ${data.processing_time?.toFixed(2)}s | <strong>Confidence:</strong> ${data.confidence||'N/A'}`;

 const lineItemsContainer=document.getElementById('lineItems');
 const itemCount=document.getElementById('itemCount');

 if(data.items&&data.items.length>0){
  lineItemsContainer.innerHTML='';
  data.items.forEach(item=>{
   const itemDiv=document.createElement('div');
   itemDiv.className='line-item';
   itemDiv.innerHTML=`<span class="item-name">${item.name}</span><span class="item-price">$${item.total_price}</span>`;
   lineItemsContainer.appendChild(itemDiv);
  });
  itemCount.textContent=data.items.length;
 }else{
  lineItemsContainer.innerHTML='<p class="no-items">No items extracted</p>';
  itemCount.textContent='0';
 }

 elements.resultsSection.classList.remove('hidden');
}

function exportData(format){
 if(!currentExtractionData){showError('No data to export');return;}

 let content,filename,mimeType;
 switch(format){
  case'json':
   content=JSON.stringify(currentExtractionData,null,2);
   filename='receipt_data.json';
   mimeType='application/json';
   break;
  case'csv':
   content=convertToCSV(currentExtractionData);
   filename='receipt_data.csv';
   mimeType='text/csv';
   break;
  case'txt':
   content=convertToText(currentExtractionData);
   filename='receipt_data.txt';
   mimeType='text/plain';
   break;
  default:return;
 }

 const blob=new Blob([content],{type:mimeType});
 const url=URL.createObjectURL(blob);
 const a=document.createElement('a');
 a.href=url;
 a.download=filename;
 a.click();
 URL.revokeObjectURL(url);
}

function convertToCSV(data){
 let csv='Item,Quantity,Price\n';
 if(data.items&&data.items.length>0){
  data.items.forEach(item=>{csv+=`"${item.name}",${item.quantity},${item.total_price}\n`;});
 }
 csv+='\nStore Information\n';
 csv+=`Name,${data.store?.name||''}\n`;
 csv+=`Address,${data.store?.address||''}\n`;
 csv+=`Phone,${data.store?.phone||''}\n`;
 csv+='\nTransaction\n';
 csv+=`Date,${data.date||''}\n`;
 csv+=`Total,${data.totals?.total||''}\n`;
 return csv;
}

function convertToText(data){
 let text='=== RECEIPT EXTRACTION ===\n\n';
 text+='--- Store Information ---\n';
 text+=`Name: ${data.store?.name||'-'}\n`;
 text+=`Address: ${data.store?.address||'-'}\n`;
 text+=`Phone: ${data.store?.phone||'-'}\n\n`;
 text+='--- Transaction Details ---\n';
 text+=`Date: ${data.date||'-'}\n`;
 text+=`Total: $${data.totals?.total||'-'}\n\n`;
 if(data.items&&data.items.length>0){
  text+='--- Line Items ---\n';
  data.items.forEach((item,index)=>{text+=`${index+1}. ${item.name} - $${item.total_price}\n`;});
 }
 text+=`\n--- Extraction Info ---\n`;
 text+=`Model: ${data.model}\n`;
 text+=`Processing Time: ${data.processing_time?.toFixed(2)}s\n`;
 return text;
}

function showLoading(show,message='Processing receipt...'){
 if(show){
  elements.loadingOverlay.classList.remove('hidden');
  const loadingText=elements.loadingOverlay.querySelector('p');
  if(loadingText)loadingText.textContent=message;
 }else{
  elements.loadingOverlay.classList.add('hidden');
 }
}

function showError(message){
 elements.errorSection.classList.remove('hidden');
 document.getElementById('errorMessage').textContent=message;
}

function showSuccess(message){
 const errorSection=elements.errorSection;
 errorSection.style.backgroundColor='#d1fae5';
 errorSection.style.borderColor='#10b981';
 errorSection.classList.remove('hidden');
 document.getElementById('errorMessage').textContent='✓ '+message;
 document.getElementById('errorMessage').style.color='#065f46';
 setTimeout(()=>{
  errorSection.style.backgroundColor='';
  errorSection.style.borderColor='';
  document.getElementById('errorMessage').style.color='';
  hideError();
 },5000);
}

function hideError(){
 elements.errorSection.classList.add('hidden');
}

document.addEventListener('DOMContentLoaded',init);
