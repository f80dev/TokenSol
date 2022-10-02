import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SelectkeyComponent } from './selectkey.component';
import {HttpClientModule} from "@angular/common/http";
import {MatSnackBarModule} from "@angular/material/snack-bar";

describe('SelectkeyComponent', () => {
  let component: SelectkeyComponent;
  let fixture: ComponentFixture<SelectkeyComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ SelectkeyComponent ],
      imports: [HttpClientModule,MatSnackBarModule]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(SelectkeyComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
