import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';

@Component({
  selector: 'app-input',
  templateUrl: './input.component.html',
  styleUrls: ['./input.component.css']
})
export class InputComponent implements OnInit {
  @Input() infobulle:string="";
  @Input() label:string="";
  @Input() label_button:string="";
  @Input() maxlength:string=""
  @Input() width:string="100%";
  @Input() value:string="";
  @Input() placeholder:string="";
  @Output() valueChange=new EventEmitter<string>();
  @Output() validate=new EventEmitter();
  @Input() value_type:string="";
  @Input() help:string="";
  @Input() help_input: string="";
  @Input() help_button: string="Enregistrez";


  constructor() { }

  ngOnInit(): void {
  }

  set input_value(val) {
    this.value=val;
    this.valueChange.emit(this.value);
  }

  get input_value() {
    return this.value;
  }

  on_cancel() {
    this.value="";
  }

  on_validate() {
    this.validate.emit(this.value);
  }

  on_key($event: KeyboardEvent) {
    if($event.key=='Enter')this.on_validate();
  }
}
