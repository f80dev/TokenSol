import {Component, Input, OnChanges, SimpleChanges} from '@angular/core';

@Component({
  selector: 'app-jauge',
  templateUrl: './jauge.component.html',
  styleUrls: ['./jauge.component.css']
})
export class JaugeComponent implements OnChanges {

  @Input() max=10;
  @Input() step=1;
  @Input() duration=20;
  @Input() activate:boolean=false;
  current: number=0;
  hInterval: NodeJS.Timeout | undefined;

  constructor() { }

  ngOnChanges(changes: SimpleChanges): void {
    if(changes["activate"].currentValue!=changes["activate"].previousValue){
      if(this.hInterval){
        this.current=0;
        clearInterval(this.hInterval);
      }
      this.hInterval=setInterval(()=>{
        this.current=this.current+this.step
        if(this.current>=this.max)this.step=0;
      },(1000*this.duration/(this.max/this.step)));
    }
  }


}
