import {Component, EventEmitter, Input, OnDestroy, OnInit, Output} from '@angular/core';
import {Observable, Subject} from "rxjs";
import jsQR from "jsqr";
import {WebcamImage} from "ngx-webcam";

@Component({
  selector: 'app-scanner',
  templateUrl: './scanner.component.html',
  styleUrls: ['./scanner.component.css']
})
export class ScannerComponent implements OnInit,OnDestroy {

  @Input("size") size="300px";
  @Input("filter") filter="";
  @Input() showCapture:boolean=false;
  @Input("caption") caption="Pointez vers le QRCode d'une adresse";
  @Output('flash') onflash: EventEmitter<any>=new EventEmitter();
  @Output('cancel') oncancel: EventEmitter<any>=new EventEmitter();
  @Output('capture') ontouch: EventEmitter<any>=new EventEmitter();
  @Input("imageQuality") imageQuality=0.85;


  private trigger: Subject<void> = new Subject<void>();
  private nextWebcam: Subject<boolean|string> = new Subject<boolean|string>();
  handle:any;
  _size: any;
  image:WebcamImage | undefined;


  constructor() {
    this._size=Number(this.size.replace("px",""));
  }

  ngOnInit() {
    this.handle=setInterval(()=>{
      this.trigger.next();
    },250);
  }

  public get triggerObservable(): Observable<void> {
    return this.trigger.asObservable();
  }

  public get nextWebcamObservable(): Observable<boolean|string> {
    return this.nextWebcam.asObservable();
  }

  stopScanner(){
    clearInterval(this.handle);
  }

  handleImage(img: WebcamImage) {
    this.image=img;
    var decoded =jsQR(img.imageData.data,img.imageData.width,img.imageData.height);
    if(decoded!=null && decoded.data!=null && (this.filter.length==0 || decoded.data.indexOf(this.filter)>-1)){
      this.onflash.emit({data:decoded.data});
    }
  }

  ngOnDestroy(): void {
    this.stopScanner();
  }

  webcamError() {
    this.oncancel.emit();
  }

  capture() {
    this.ontouch.emit({data:"data:image/jpeg;base64,"+this.image?.imageAsBase64})
  }
}
