import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DealermachineComponent } from './dealermachine.component';
import {HttpClientModule} from "@angular/common/http";
import {RouterTestingModule} from "@angular/router/testing";
import {MatSnackBarModule} from "@angular/material/snack-bar";
import {AliasPipe} from "../alias.pipe";

describe('DealermachineComponent', () => {
  let component: DealermachineComponent;
  let fixture: ComponentFixture<DealermachineComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ DealermachineComponent ],
      imports: [HttpClientModule,RouterTestingModule,MatSnackBarModule],
      providers: [AliasPipe]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(DealermachineComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
