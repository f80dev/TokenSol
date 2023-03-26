import {Component, EventEmitter, Input, OnDestroy, OnInit, Output} from '@angular/core';
import {Observable, Subject} from "rxjs";
import jsQR from "jsqr";

@Component({
  selector: 'app-scanner',
  templateUrl: './scanner.component.html',
  styleUrls: ['./scanner.component.css']
})
export class ScannerComponent implements OnInit,OnDestroy {

  @Input("size") size="300px";
  @Input("filter") filter="";
  @Input("caption") caption="Pointez vers le QRCode d'une adresse";
  @Output('flash') onflash: EventEmitter<any>=new EventEmitter();
  @Output('cancel') oncancel: EventEmitter<any>=new EventEmitter();
  @Output('capture') ontouch: EventEmitter<any>=new EventEmitter();
  @Input("imageQuality") imageQuality=0.85;


  private trigger: Subject<void> = new Subject<void>();
  private nextWebcam: Subject<boolean|string> = new Subject<boolean|string>();
  handle:any;
  _size: any;
  image:any;


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

  handleImage(event: any) {
    var rc=event.imageData;
    this.image=event.imageData;
    var decoded =jsQR(rc.data,rc.width,rc.height);
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
    this.ontouch.emit({data:this.image})
  }
}
