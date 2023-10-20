import {Component, EventEmitter, Input, OnChanges, OnDestroy, OnInit, Output, SimpleChanges} from '@angular/core';
import {Router} from "@angular/router";
import {hashCode} from "../../tools";

@Component({
  selector: 'app-tuto',
  templateUrl: './tuto.component.html',
  styleUrls: ['./tuto.component.css']
})
export class TutoComponent implements OnChanges,OnInit,OnDestroy {

  @Input("align") text_align: string="center";
  @Input() align_image: string="center";
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
  // @Input('if') _if=true;
  @Input('fullscreen') fullscreen=true;
  @Input('image') image: string="";
  @Input('main_button') labelButton: string="";
  @Input('icon') icon:string="tips_and_updates";
  @Input('color') color:string="";
  @Input() opacity=0.8;
  @Input('force') force:boolean=false;
  @Input('faq') faq:string="";
  @Input('icon_button') _button:string="";
  @Input('height') height:string="auto";
  @Output('click') onclick: EventEmitter<any>=new EventEmitter();
  @Output('close') onclose: EventEmitter<any>=new EventEmitter();
  handle: any;


  constructor(public router:Router) {}

  code:string="";
  _position="absolute";
  text_to_show=""
  showButton: boolean=false
  background_style:any={
    display: 'block',
    opacity: 1,
    textAlign:'center',
    top:'0',
    left:'0',
    width:'100vw',
    height:'100vh',
    zIndex:100000
  }
  contentStyle:any={opacity: 1,display:"block",position:"fixed",left:0,top:0,width:"100vw",height:"100vh",zIndex:10000000}



  refresh() {

    if(!this.fullscreen)this._position="relative";

    if(this._type=="title" && this.title=="")this.title=this.label;

    if(this.title!=null && this.title.length>0 || this.subtitle.length>0){
      this._type="title";
      this.label=this.title;
    }
    if(this._type=="tips") {
      if(this.icon!='')this.image="";
      if (this._button != null && this._button.length > 0) this.image = "";
    }

    if(this.color==''){
      if(this._type=="tips")this.color="#ecdb95"
      if(this._type=="title")this.color="white";
    }
    this.background_style.color=this.color

    if(this.bkColor!='')this.background_style.backgroundColor=this.bkColor
    if(this.background!=''){
      this.background_style.backgroundImage="url("+this.background+")"
      this.background_style.backgroundSize="cover"
      this.background_style.filter="blur(1px) brightness(50%)"
      this.background_style.backgroundPosition=this.align_image+" center"
    }

    this.background_style.position=this._position

    this.code="histo"+hashCode(this.label+this.subtitle);
    if(!this.force){
      if((localStorage.getItem("tuto") || "").indexOf(this.code)>-1){
        this.hideTuto();
      } else {
        localStorage.setItem("tuto",(localStorage.getItem("tuto") || "")+","+this.code);
      }
    }

    if(this.duration==0)this.duration=(this.label.split(" ").length+this.subtitle.split(" ").length)/2;
    if(this.duration>0){
      this.handle=setTimeout(()=>{this.hideTuto()},(2+this.duration+this.delay)*1000);
    }
    setTimeout(()=>{this.showButton=true},2000+this.delay*1000)

    //setTimeout(()=>{this.text_to_show=this.label},this.delay*1000)

  }

  async ngOnInit() {
    if (this.delay > 0) {
      this.contentStyle={opacity:0}
      setTimeout(() => {
        this.contentStyle = {opacity: 1}
      }, this.delay * 1000);
    } else {
      this.contentStyle={opacity:1}
    }
  }


  ngOnChanges(changes: SimpleChanges) {
    this.refresh();
  }


  hideTuto() {//Marque l'affichage
    if(this._type=="tips")this.label=""
    this.onclose.emit();
  }

  ngOnDestroy(): void {
    clearTimeout(this.handle);
  }


}
