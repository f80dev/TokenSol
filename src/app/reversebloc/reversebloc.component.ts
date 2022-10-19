import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';

@Component({
  selector: 'app-reversebloc',
  templateUrl: './reversebloc.component.html',
  styleUrls: ['./reversebloc.component.scss']
})
export class ReverseblocComponent implements OnInit {

  @Input() image="";
  @Input() data:any={};
  @Input() width="300px";
  @Input() minwidth="350px";
  @Input() maxwidth="450px";
  @Input() height="300px";
  @Input() reverse=false;

  @Output() onreverse: EventEmitter<any>=new EventEmitter();

  constructor() { }

  ngOnInit(): void {
  }


  on_reverse(side=true){
    this.onreverse.emit({data:this.data,side:true});
  }


}
