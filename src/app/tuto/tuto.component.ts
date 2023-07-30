import {Component, EventEmitter, Input, OnChanges, OnInit, Output, SimpleChanges} from '@angular/core';
import {Router} from "@angular/router";
import {hashCode} from "../../tools";

@Component({
  selector: 'app-tuto',
  templateUrl: './tuto.component.html',
  styleUrls: ['./tuto.component.css']
})
export class TutoComponent implements OnInit,OnChanges {

  @Input("text-align") text_align: string="center";
  @Input("title") title: string="";
  @Input("width") width: string="auto";
  @Input("type") _type: string="tips";
  @Input("label") label: string="";
  @Input("subtitle")subtitle: string="";
  @Input("position") position: string="center";
  @Input("delay") delay=0.1;
  @Input("duration") duration=0;
  @Input("background") background="";
  @Input("background-color") bkColor="black";
  @Input('if') _if=true;
  @Input('fullscreen') fullscreen=true;
  @Input('image') image: string="";
  @Input('main_button') labelButton: string="Continuez";
  @Input('icon') icon:string="tips_and_updates";
  @Input('color') color:string="white";
  @Input('force') force:boolean=false;
  @Input('faq') faq:string="";
  @Input('icon_button') _button:string="";
  @Input('height') height:string="auto";
  @Output('click') onclick: EventEmitter<any>=new EventEmitter();
  @Output('close') onclose: EventEmitter<any>=new EventEmitter();
  visibleTuto: boolean=true

  constructor(public router:Router) {}

  handle:any;
  code:string="";
  _position="fixed";
  text_to_show=""

  refresh(){

    if(this.icon!=null && this.icon.length>0)this.image="";

    if(this.title!=null && this.title.length>0 || this.subtitle.length>0){
      this._type="title";
      this.label=this.title;
    }
    if(this._type=="tips" && this._button!=null && this._button.length>0)this.image="";

    this.code="histo"+hashCode(this.label+this.subtitle);
    if(!this.force){
      if((localStorage.getItem("tuto") || "").indexOf(this.code)>-1){
        this.label="";
      } else {
        localStorage.setItem("tuto",(localStorage.getItem("tuto") || "")+","+this.code);
      }
    }

    if(this.duration==0)this.duration=(this.label.split(" ").length+this.subtitle.split(" ").length)/2;

    setTimeout(()=>{this.text_to_show=this.label},this.delay*1000)
    setTimeout(()=>{this.text_to_show="";},(2+this.duration+this.delay)*1000);

    if(!this.fullscreen)this._position="relative";

    if(this._type=="title" || this.force ){
      if(this._if){
        this.visibleTuto=true;
      } else {
        this.hideTuto();
      }
    }
    else{
      this.hideTuto();
    }

    if(this._type!="title")this.color="#ecdb95";

  }



  ngOnChanges(changes: SimpleChanges) {
    this.refresh();
  }


  hideTuto() {//Marque l'affichage
    this.text_to_show="";
    this._if=false;
    this.visibleTuto=false;
    this.title="";
    this.subtitle="";
    this.onclose.emit();
    clearTimeout(this.handle);
  }


  ngOnInit(): void {

  }

  showText(b: boolean) {
    this._if=b;
  }
}
