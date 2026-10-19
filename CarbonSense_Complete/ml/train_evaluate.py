"""Train/evaluate on a labelled CSV. Synthetic datasets must be reported as synthetic."""
import argparse, json
from pathlib import Path
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import GroupShuffleSplit, train_test_split
import joblib

FEATURES = ["voltage_v", "current_ma", "power_mw", "energy_wh", "temperature_c", "duty_cycle_pct"]
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--data",required=True); p.add_argument("--out",required=True)
    args=p.parse_args()
    df=pd.read_csv(args.data)
    required=set(FEATURES+["load_label","run_id","data_origin"])
    missing=required-set(df.columns)
    if missing: raise SystemExit(f"Missing columns: {sorted(missing)}")
    df=df.dropna(subset=["load_label"])
    if df.load_label.nunique()<2: raise SystemExit("Need at least two load classes.")
    X=df[FEATURES]; y=df["load_label"].astype(str)
    groups=df["run_id"].astype(str)
    if groups.nunique()>=4:
        splitter=GroupShuffleSplit(n_splits=1,test_size=.25,random_state=42)
        tr,te=next(splitter.split(X,y,groups))
    else:
        tr,te=train_test_split(range(len(df)),test_size=.25,random_state=42,stratify=y)
    numeric=Pipeline([("imputer",SimpleImputer(strategy="median")),("scale",StandardScaler())])
    pre=ColumnTransformer([("num",numeric,FEATURES)])
    model=Pipeline([("preprocess",pre),("classifier",RandomForestClassifier(n_estimators=250,class_weight="balanced",random_state=42,min_samples_leaf=2))])
    model.fit(X.iloc[tr],y.iloc[tr]); pred=model.predict(X.iloc[te])
    report=classification_report(y.iloc[te],pred,output_dict=True,zero_division=0)
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    joblib.dump(model,out/"load_classifier.joblib")

    # Separate unsupervised detector: fit only on training rows explicitly labelled normal.
    # If a dataset lacks anomaly_label, treat training data as baseline but record that limitation.
    normal_mask = (df["anomaly_label"].astype(str).str.lower().isin(["normal", "0", "false"])) if "anomaly_label" in df.columns else pd.Series(True,index=df.index)
    normal_train = [idx for idx in tr if bool(normal_mask.iloc[idx])]
    detector_source = "rows labelled normal" if "anomaly_label" in df.columns else "all training rows (no anomaly labels supplied)"
    anomaly_detector = Pipeline([("preprocess",pre),("detector",IsolationForest(n_estimators=250,contamination="auto",random_state=42))])
    anomaly_detector.fit(X.iloc[normal_train] if len(normal_train)>=20 else X.iloc[tr])
    anomaly_pred = anomaly_detector.predict(X.iloc[te])  # -1 unusual, +1 inlier
    joblib.dump(anomaly_detector,out/"anomaly_detector.joblib")
    anomaly_summary={"test_rows":len(te),"flagged_rows":int((anomaly_pred==-1).sum()),
      "flagged_fraction":float((anomaly_pred==-1).mean()),"training_baseline":detector_source,
      "interpretation":"Unusual relative to training distribution; not proof of waste or a fault."}
    metadata={"data_file":str(Path(args.data)),"data_origin_values":sorted(df.data_origin.astype(str).unique().tolist()),
      "rows":len(df),"runs":int(groups.nunique()),"classes":sorted(y.unique().tolist()),
      "split":"GroupShuffleSplit by run_id" if groups.nunique()>=4 else "random stratified split (few run groups)",
      "accuracy":float(accuracy_score(y.iloc[te],pred)),"classification_report":report,
      "confusion_matrix":confusion_matrix(y.iloc[te],pred,labels=sorted(y.unique())).tolist(),
      "anomaly_detection":anomaly_summary,
      "warning":"If data_origin is simulated, all metrics are software-development checks only, not hardware validation or proof of real-world accuracy."}
    (out/"evaluation.json").write_text(json.dumps(metadata,indent=2))
    print(json.dumps({k:metadata[k] for k in ["data_origin_values","rows","runs","classes","split","accuracy","anomaly_detection","warning"]},indent=2))
if __name__=="__main__": main()
