import {AfterViewInit, Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import {animate, style, transition, trigger} from "@angular/animations";


//voir https://medium.com/cloud-native-the-gathering/how-to-use-css-to-fade-in-and-fade-out-html-text-and-pictures-f45c11364f08
const leaveTrans = transition(':leave', [
  style({opacity: 1}),
  animate('2s ease-out', style({opacity: 0}))
])

const fadeOut = trigger('fadeOut', [leaveTrans]);

@Component({
  selector: 'app-splash',
  templateUrl: './splash.component.html',
  styleUrls: ['./splash.component.css'],
  animations: [fadeOut]
})
export class SplashComponent implements OnInit,AfterViewInit {
  @Input() appname: any;
  @Input() filter="";
  @Input() duration=2000;
  @Input() description: any;
  @Input() image: string="";
  @Output('terminate') onterminate: EventEmitter<any>=new EventEmitter();
  animate: string="";
  show=0;

  constructor() { }

  ngOnInit(): void {

  }

  ngAfterViewInit(): void {
    let delay=(this.image.length>0) ? 300 : 4000;
    setTimeout(()=>{
      this.show=1;
      if(!this.duration)this.duration=2000;
      if(this.duration>0){
        setTimeout(()=>{
          this.show=2;
          this.onterminate.emit(true);

        },this.duration)
      } else {
        this.show=2;
      }

      },300);
  }

}
