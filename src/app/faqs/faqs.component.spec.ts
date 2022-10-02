import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FaqsComponent } from './faqs.component';
import {HttpClientModule} from "@angular/common/http";
import {RouterTestingModule} from "@angular/router/testing";
import {MatSnackBarModule} from "@angular/material/snack-bar";

describe('FaqsComponent', () => {
  let component: FaqsComponent;
  let fixture: ComponentFixture<FaqsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ FaqsComponent ],
      imports: [HttpClientModule,RouterTestingModule,MatSnackBarModule]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(FaqsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
