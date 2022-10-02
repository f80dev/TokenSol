import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ValidateComponent } from './validate.component';
import {HttpClientModule} from "@angular/common/http";
import {RouterTestingModule} from "@angular/router/testing";
import {MatSnackBarModule} from "@angular/material/snack-bar";
import {AliasPipe} from "../alias.pipe";

describe('ValidateComponent', () => {
  let component: ValidateComponent;
  let fixture: ComponentFixture<ValidateComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ValidateComponent ],
      imports: [HttpClientModule,RouterTestingModule,MatSnackBarModule],
      providers:[{provide:AliasPipe}]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ValidateComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
